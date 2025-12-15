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

@router.get("/school_admin", response_class=HTMLResponse)
def school_admin_dashboard(request: Request, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if current_user.role != UserRole.SCHOOL_ADMIN:
         return templates.TemplateResponse("error.html", {"request": request, "error": "Acceso restringido a Directores."})
    
    if not current_user.school_id:
        return templates.TemplateResponse("error.html", {"request": request, "error": "No estás asignado a ningún centro."})

    # 1. Obtener todos los alumnos del centro
    students = db.query(Student).filter(Student.school_id == current_user.school_id).all()
    
    # 2. Agrupar por Aula
    from collections import defaultdict
    classrooms = defaultdict(lambda: {"students": [], "alerts": 0, "status": "green"})
    
    total_alerts_global = 0
    
    for s in students:
        # Asegurar clave (si no tiene clase, 'Sin Asignar')
        c_name = s.grade_class if s.grade_class else "Sin Asignar"
        classrooms[c_name]["students"].append(s)
        
        # Check high risk surveys for this student
        high_risk_surveys = db.query(SurveyResponse).filter(
            SurveyResponse.student_id == s.id,
            SurveyResponse.risk_level.in_([AlertLevel.HIGH, AlertLevel.CRITICAL])
        ).count()
        
        classrooms[c_name]["alerts"] += high_risk_surveys
        total_alerts_global += high_risk_surveys

    # 3. Determinar Estado por Aula
    classroom_list = []
    
    # Pre-fetch Critical alerts for this school to avoid N+1 inside loop if possible 
    # (Actually we are doing N+1 counts inside loop above, let's optimize if needed, 
    # but for now let's just fix the logic for Red Dot)
    
    for name, data in classrooms.items():
        count = len(data["students"])
        alerts = data["alerts"]
        
        # Check specific risks for this class
        # We need to know if ANY is critical for the Red Dot
        has_critical = False
        for s in data["students"]:
             # This is N*M, but M is small (surveys per student usually 1 active)
             # Better: Query above should store risks
             pass 
        
        # Re-query specifically for Critical Count to be sure
        critical_count = db.query(SurveyResponse).join(Student).filter(
            Student.grade_class == name,
            Student.school_id == current_user.school_id,
            SurveyResponse.risk_level == AlertLevel.CRITICAL
        ).count()

        has_critical = critical_count > 0

        # Status Logic
        status_color = "green"
        if has_critical:
            status_color = "red" # 1 Critical = Red
        elif alerts > 0:
            status_color = "orange" # Any High/Critical = Orange (if not captured by above)
            
        classroom_list.append({
            "name": name,
            "student_count": count,
            "alerts_count": alerts,
            "status": status_color,
            "has_critical": has_critical
        })
        
    # Ordenar por alertas descendente
    classroom_list.sort(key=lambda x: x["alerts_count"], reverse=True)

    # Estado Global del Centro
    school_status = "Saludable"
    school_color = "green"
    if any(c["status"] == "red" for c in classroom_list):
        school_status = "Riesgo Alto Detectado"
        school_color = "red"
    elif any(c["status"] == "orange" for c in classroom_list):
        school_status = "Precaución"
        school_color = "orange"

    return templates.TemplateResponse("dashboard/school_admin_view.html", {
        "request": request,
        "user": current_user,
        "school": current_user.school,
        "total_students": len(students),
        "total_alerts": total_alerts_global,
        "school_status": school_status,
        "school_color": school_color,
        "classrooms": classroom_list
    })

@router.get("/school_admin/classroom/{grade_class}", response_class=HTMLResponse)
def classroom_detail_view(request: Request, grade_class: str, school_id: int = None, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    
    target_school_id = None

    if current_user.role == UserRole.SCHOOL_ADMIN:
        target_school_id = current_user.school_id
    elif current_user.role == UserRole.SUPER_ADMIN:
        if not school_id:
             return templates.TemplateResponse("error.html", {"request": request, "error": "Falta el ID del centro."})
        target_school_id = school_id
    else:
         return templates.TemplateResponse("error.html", {"request": request, "error": "Acceso restringido."})
         
    # Obtener alumnos de esa clase y centro
    students = db.query(Student).filter(
        Student.school_id == target_school_id,
        Student.grade_class == grade_class
    ).all()
    
    # Obtener sus casos (encuestas)
    cases = []
    for s in students:
        surveys = db.query(SurveyResponse).filter(
            SurveyResponse.student_id == s.id
        ).order_by(desc(SurveyResponse.date_submitted)).all()
        for surv in surveys:
            cases.append(surv)
            
    # Ordenar casos por fecha
    cases.sort(key=lambda x: x.date_submitted, reverse=True)

    return templates.TemplateResponse("dashboard/classroom_detail.html", {
        "request": request,
        "user": current_user,
        "grade_class": grade_class,
        "cases": cases
    })

@router.get("/case/{survey_id}", response_class=HTMLResponse)
def view_case_details(request: Request, survey_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    # Validar rol
    if current_user.role not in [UserRole.TEACHER, UserRole.SCHOOL_ADMIN, UserRole.SUPER_ADMIN]:
         return templates.TemplateResponse("error.html", {"request": request, "error": "No autorizado"})
    
    survey = db.query(SurveyResponse).filter(SurveyResponse.id == survey_id).first()
    if not survey:
        raise HTTPException(status_code=404, detail="Caso no encontrado")
        
    # Validar que el alumno pertenece al contexto del usuario
    authorized = False
    if current_user.role == UserRole.TEACHER:
        if survey.student.teacher_id == current_user.id:
            authorized = True
    elif current_user.role == UserRole.SCHOOL_ADMIN:
        if survey.student.school_id == current_user.school_id:
            authorized = True
    elif current_user.role == UserRole.SUPER_ADMIN:
        authorized = True
            
    if not authorized:
         return templates.TemplateResponse("error.html", {"request": request, "error": "No tienes permiso para ver este caso."})
         
    return templates.TemplateResponse("dashboard/case_details.html", {
        "request": request, 
        "user": current_user,
        "survey": survey
    })

# --- SUPER ADMIN DASHBOARD ---
@router.get("/super_admin", response_class=HTMLResponse)
def super_admin_dashboard(request: Request, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if current_user.role != UserRole.SUPER_ADMIN:
         return templates.TemplateResponse("error.html", {"request": request, "error": "Acceso restringido a Conselleria."})
    
    # Obtener TODOS los centros
    from ..models import School, Student
    from sqlalchemy.orm import joinedload
    
    # Eager load students to optimize and allow sorting
    # Note: With 2000 schools, this might be heavy, but only ~40 have students.
    schools = db.query(School).options(joinedload(School.students)).all()
    
    # Sort by student count descending so active schools show first
    schools.sort(key=lambda s: len(s.students), reverse=True)
    
    # Calculate statuses for List View (Same logic as Map)
    school_status_map = {}
    
    # Optimized Status Queries
    from collections import defaultdict
    from ..models import SurveyResponse, AlertLevel
    # Query: SchoolID, GradeClass, RiskLevel
    student_risks = db.query(
        Student.school_id, 
        Student.grade_class,
        SurveyResponse.risk_level
    ).join(SurveyResponse).all()
    
    # Map: school_id -> list of risks
    risk_map = defaultdict(list)
    # Map: school_id -> classroom_name -> has_critical (bool)
    classroom_critical_map = defaultdict(lambda: defaultdict(bool))

    for s_id, g_class, r_level in student_risks:
        risk_map[s_id].append(r_level)
        if r_level == AlertLevel.CRITICAL:
            classroom_critical_map[s_id][g_class] = True
    
    for school in schools:
        status = "green"
        if school.id in risk_map:
            risks = risk_map[school.id]
            if AlertLevel.CRITICAL in risks:
                status = "red"
            elif AlertLevel.HIGH in risks:
                status = "orange"
        school_status_map[school.id] = status

    return templates.TemplateResponse("dashboard/super_admin_view.html", {
        "request": request,
        "user": current_user,
        "schools": schools,
        "statuses": school_status_map,
        "classroom_risks": classroom_critical_map
    })

# --- MAPA ---

@router.get("/map", response_class=HTMLResponse)
def map_view(request: Request, current_user: User = Depends(get_current_user)):
    # Accesible SOLO para Conselleria (SUPER_ADMIN)
    if current_user.role != UserRole.SUPER_ADMIN:
         return templates.TemplateResponse("error.html", {"request": request, "error": "Acceso restringido. Solo Conselleria puede ver el mapa global."})

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
    from sqlalchemy import or_

    # 1. Obtener SOLO los colegios con estudiantes y coordenadas (Query 1)
    # User Request: "Solo muestra en el mapa los centros que tengan estudiantes asociados"
    from ..models import Student
    schools = db.query(School).join(Student).filter(
        School.latitude.isnot(None),
        School.longitude.isnot(None)
    ).distinct().all()
    
    # 2. Obtener TODAS las encuestas con datos clave (Query 2)
    # Seleccionamos solo lo necesario para el analisis
    # Esto evita N+1 queries. Traemos school_id y grade_class
    results = db.query(
        Student.school_id, 
        Student.grade_class,
        SurveyResponse.risk_level
    ).join(SurveyResponse).all()
    
    # 3. Estructurar datos para acceso rápido O(1)
    # school_id -> grade_class -> list of risk_levels
    school_map = defaultdict(lambda: defaultdict(list))
    
    for row in results:
        s_id = row[0]
        g_class = row[1] if row[1] else "Unknown"
        r_level = row[2]
        school_map[s_id][g_class].append(r_level)

    features = []
    
    # 4. Procesar cada colegio (Todo en memoria)
    for school in schools:
        traffic_light = "green"
        
        # Check si tenemos datos para este colegio
        if school.id in school_map:
            class_groups = school_map[school.id]
            
            is_school_red = False
            is_school_orange = False
            
            # Flatten all risks for the school to check indiscriminately across classes
            # User Rule: "Si un cole tiene algún caso crítico, debe aparecer como crítico (color rojo)"
            all_risks = []
            for r_list in class_groups.values():
                all_risks.extend(r_list)

            if AlertLevel.CRITICAL in all_risks:
                is_school_red = True
            elif AlertLevel.HIGH in all_risks:
                is_school_orange = True
            else:
                 # Check strict percentage for Mediums? Or keep Green if only Low/Medium?
                 # Let's keep existing percentage logic for lighter colors if needed, 
                 # but for Red/Orange we are strict now.
                 pass

            if is_school_red:
                traffic_light = "red"
            elif is_school_orange:
                traffic_light = "orange"
        
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
