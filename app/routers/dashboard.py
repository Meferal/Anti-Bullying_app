from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from sqlalchemy import desc
from ..database import get_db
from ..models import Student, SurveyResponse, AlertLevel

router = APIRouter(prefix="/dashboard", tags=["dashboard"])
templates = Jinja2Templates(directory="app/templates")

from ..security import get_current_user
from ..models import User, UserRole

@router.get("/teacher", response_class=HTMLResponse)
def teacher_dashboard(request: Request, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    # Verificar rol
    if current_user.role not in [UserRole.TEACHER, UserRole.SCHOOL_ADMIN]:
         return templates.TemplateResponse("error.html", {"request": request, "error": "Acceso restringido a profesores."})
    
    teacher = current_user

    # 1. Obtener métricas generales (SOLO de sus alumnos asignados)
    total_students = db.query(Student).filter(Student.teacher_id == teacher.id).count()
    
    # 2. Buscar alertas recientes (Riesgo Alto o Crítico) DE SUS ALUMNOS
    critical_alerts = db.query(SurveyResponse).join(Student).filter(
        Student.teacher_id == teacher.id,
        SurveyResponse.risk_level.in_([AlertLevel.HIGH, AlertLevel.CRITICAL])
    ).order_by(desc(SurveyResponse.date_submitted)).all()
    
    # 3. Datos para la tabla principal (Últimas encuestas) DE SUS ALUMNOS
    recent_activity = db.query(SurveyResponse).join(Student).filter(
        Student.teacher_id == teacher.id
    ).order_by(desc(SurveyResponse.date_submitted)).limit(20).all()
    
    # 4. Calcular Estadísticas Reales
    # Porcentaje de encuestas "Saludables" (LOW Risk) recientes
    total_surveys = len(recent_activity)
    healthy_count = sum(1 for s in recent_activity if s.risk_level == AlertLevel.LOW)
    healthy_percentage = int((healthy_count / total_surveys * 100)) if total_surveys > 0 else 100

    return templates.TemplateResponse("dashboard/teacher_view.html", {
        "request": request,
        "user": current_user, 
        "teacher": teacher, 
        "total_students": total_students,
        "critical_count": len(critical_alerts),
        "healthy_percentage": healthy_percentage,
        "alerts": critical_alerts,
        "activity": recent_activity
    })

@router.get("/case/{survey_id}", response_class=HTMLResponse)
def view_case_details(request: Request, survey_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    # Validar rol
    if current_user.role not in [UserRole.TEACHER, UserRole.SCHOOL_ADMIN]:
         return templates.TemplateResponse("error.html", {"request": request, "error": "No autorizado"})
    
    survey = db.query(SurveyResponse).filter(SurveyResponse.id == survey_id).first()
    if not survey:
        raise HTTPException(status_code=404, detail="Caso no encontrado")
        
    # Validar que el alumno pertenece al profe (opcional, pero recomendado)
    if survey.student.teacher_id != current_user.id:
         return templates.TemplateResponse("error.html", {"request": request, "error": "Este caso no pertenece a tus alumnos asignados"})
         
    return templates.TemplateResponse("dashboard/case_details.html", {
        "request": request, 
        "user": current_user,
        "survey": survey
    })

# --- MAPA ---

@router.get("/map", response_class=HTMLResponse)
def map_view(request: Request, current_user: User = Depends(get_current_user)):
    # Accesible SOLO para profesores y administradores
    if current_user.role not in [UserRole.TEACHER, UserRole.SCHOOL_ADMIN]:
         return templates.TemplateResponse("error.html", {"request": request, "error": "Acceso restringido a docentes."})

    return templates.TemplateResponse("dashboard/map.html", {
        "request": request,
        "user": current_user, 
    })

    return JSONResponse(content=geojson)

    return JSONResponse(content=geojson)

@router.get("/api/schools_geojson")
def get_schools_geojson(db: Session = Depends(get_db)):
    from ..models import School, User, UserRole, SurveyResponse, Student
    from fastapi.responses import JSONResponse
    from collections import defaultdict
    
    # 1. Filtrar colegios: Solo los que tienen algún usuario activo (Profe o Admin o Padre)
    # y geolocalización válida
    from sqlalchemy import or_
    schools_with_teachers = db.query(School).join(User).filter(
        # User.role.in_([UserRole.TEACHER, UserRole.SCHOOL_ADMIN, UserRole.PARENT]), # Broaden scope
        School.latitude.isnot(None),
        School.longitude.isnot(None)
    ).distinct().all()
    
    features = []
    for school in schools_with_teachers:
        # Obtenemos todas las encuestas
        surveys = db.query(SurveyResponse).join(Student).filter(
            Student.school_id == school.id
        ).all()
        
        traffic_light = "green" # Default
        
        if surveys:
            # 2. Agrupar por Aula (grade_class)
            class_groups = defaultdict(list)
            for s in surveys:
                # Usamos una clave segura, si no tiene clase asignada lo ponemos en 'Unknown'
                key = s.student.grade_class if s.student.grade_class else "Unknown"
                class_groups[key].append(s)
            
            # 3. Analizar cada Aula INDIVIDUALMENTE
            is_school_red = False
            is_school_orange = False
            
            for class_name, class_surveys in class_groups.items():
                total_class = len(class_surveys)
                if total_class == 0: continue
                
                high_risk_class = sum(1 for s in class_surveys if s.risk_level in [AlertLevel.HIGH, AlertLevel.CRITICAL])
                class_risk_pct = (high_risk_class / total_class) * 100
                
                # REGLA: Si hay al menos un aula con codigo rojo (>20% riesgo), el centro es ROJO.
                if class_risk_pct > 20:
                    is_school_red = True
                    break # Prioridad maxima, salimos
                
                if class_risk_pct > 5:
                    is_school_orange = True
            
            if is_school_red:
                traffic_light = "red"
            elif is_school_orange:
                traffic_light = "orange"
            else:
                # Fallback: Check Global stats just in case, or keep green if classes are fine
                # Si queremos mantener la logica global tambien:
                total_global = len(surveys)
                high_global = sum(1 for s in surveys if s.risk_level in [AlertLevel.HIGH, AlertLevel.CRITICAL])
                if (high_global / total_global * 100) > 5:
                     traffic_light = "orange" # Al menos naranja si el global es malo
        
        features.append({
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [school.longitude, school.latitude]
            },
            "properties": {
                "id": school.id,
                "name": school.name,
                "code": school.center_code,
                "address": school.address,
                "status": traffic_light
            }
        })
        
    geojson = {
        "type": "FeatureCollection",
        "features": features
    }
    
    return JSONResponse(content=geojson)
