from fastapi import APIRouter, Depends, Request, HTTPException, Body
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from sqlalchemy import desc
from collections import defaultdict
from ..database import get_db
from ..models import Student, SurveyResponse, AlertLevel

router = APIRouter(prefix="/dashboard", tags=["dashboard"])
templates = Jinja2Templates(directory="app/templates")

from ..security import get_current_user
from ..models import User, UserRole

# OPTIMIZATION HELPER
from sqlalchemy import func, literal_column
def get_latest_risks_bulk(db: Session, student_ids: list[int]) -> list[tuple[int, AlertLevel]]:
    """
    Returns a list of (student_id, risk_level) for the top 2 most recent surveys 
    for each student in the provided list.
    """
    if not student_ids:
        return []

    # Window Function to rank surveys per student by date
    # row_number() over (partition by student_id order by date_submitted desc)
    subquery = db.query(
        SurveyResponse.student_id,
        SurveyResponse.risk_level,
        func.row_number().over(
            partition_by=SurveyResponse.student_id,
            order_by=desc(SurveyResponse.date_submitted)
        ).label("rn")
    ).filter(
        SurveyResponse.student_id.in_(student_ids)
    ).subquery()

    # Filter for only top 2
    results = db.query(
        subquery.c.student_id,
        subquery.c.risk_level
    ).filter(
        subquery.c.rn <= 2
    ).all()
    
    return results

@router.get("/teacher", response_class=HTMLResponse)
def teacher_dashboard(request: Request, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    # Verificar rol
    if current_user.role not in [UserRole.TEACHER, UserRole.SCHOOL_ADMIN]:
         return templates.TemplateResponse("error.html", {"request": request, "error": "Acceso restringido a profesores."})
    
    teacher = current_user

    # 1. Obtener métricas generales (SOLO de sus alumnos asignados)
    total_students = db.query(Student).filter(Student.teacher_id == teacher.id).count()
    
    # 2. Buscar alertas recientes (Riesgo Alto o Crítico) DE SUS ALUMNOS
    # 2. Buscar alertas recientes (Riesgo Alto o Crítico)
    # REGLA: Solo considerar incidencias en los 2 últimos registros de cada alumno
    my_students = db.query(Student).filter(Student.teacher_id == teacher.id).all()
    critical_alerts = []
    
    for student in my_students:
        # Traer las 2 últimas encuestas de este alumno
        last_surveys = db.query(SurveyResponse).filter(
            SurveyResponse.student_id == student.id
        ).order_by(desc(SurveyResponse.date_submitted)).limit(2).all()
        
        # Si alguna de esas 2 es HIGH/CRITICAL, la añadimos
        for s in last_surveys:
            if s.risk_level in [AlertLevel.HIGH, AlertLevel.CRITICAL]:
                critical_alerts.append(s)
    
    # Ordenar por fecha globalmente para mostrar las más recientes primero
    critical_alerts.sort(key=lambda x: x.date_submitted, reverse=True)
    
    # 3. Datos para la tabla principal (Últimas encuestas) DE SUS ALUMNOS
    recent_activity = db.query(SurveyResponse).join(Student).filter(
        Student.teacher_id == teacher.id
    ).order_by(desc(SurveyResponse.date_submitted)).all()
    
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
    # 2. Agrupar por Aula
    classrooms = defaultdict(lambda: {"students": [], "alerts": 0, "status": "green"})
    
    total_alerts_global = 0
    
    # Pre-fetch recent risks for ALL students in this school
    student_ids = [s.id for s in students]
    bulk_risks = get_latest_risks_bulk(db, student_ids)
    
    # Map risks to student_id
    # student_id -> list of risk_levels (max 2)
    student_risk_map = defaultdict(list)
    for sid, r_level in bulk_risks:
        student_risk_map[sid].append(r_level)

    for s in students:
        # Asegurar clave
        c_name = s.grade_class if s.grade_class else "Sin Asignar"
        classrooms[c_name]["students"].append(s)
        
        # Check high risk surveys (from optimized map)
        risks = student_risk_map.get(s.id, [])
        high_risk_surveys = 0
        for r in risks:
            if r in [AlertLevel.HIGH, AlertLevel.CRITICAL]:
                high_risk_surveys += 1
        
        classrooms[c_name]["alerts"] += high_risk_surveys
        total_alerts_global += high_risk_surveys

    # 3. Determinar Estado por Aula
    classroom_list = []
    
    for name, data in classrooms.items():
        count = len(data["students"])
        alerts = data["alerts"]
        
        # Check Criticals (using the same optimized map)
        has_critical = False
        for stud in data["students"]:
             stud_risks = student_risk_map.get(stud.id, [])
             if AlertLevel.CRITICAL in stud_risks:
                 has_critical = True
                 break

        # Status Logic
        status_color = "green"
        if has_critical:
            status_color = "red" 
        elif alerts > 0:
            status_color = "orange"
            
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
    # --- DASHBOARD METRICS CALCULATION ---
    total_students = len(students)
    
    # 1. Active Alerts (Last 2 Surveys Rule)
    # Optimized using helper
    active_alerts_count = 0
    students_with_alerts = 0
    
    student_ids = [s.id for s in students]
    bulk_risks = get_latest_risks_bulk(db, student_ids)
    
    # Map risks to student to count
    student_risk_map = defaultdict(list)
    for sid, r in bulk_risks:
        student_risk_map[sid].append(r)
        
    for s in students:
        risks = student_risk_map.get(s.id, [])
        has_alert = False
        for r in risks:
            if r in [AlertLevel.HIGH, AlertLevel.CRITICAL]:
                active_alerts_count += 1
                has_alert = True
        
        if has_alert:
            students_with_alerts += 1

    # Healthy Percentage: (Total Students - Students with Alerts) / Total Students
    healthy_percentage = 0
    if total_students > 0:
        healthy_percentage = int(((total_students - students_with_alerts) / total_students) * 100)
    else:
        healthy_percentage = 100

    # 2. Teacher Name
    teacher_name = "Sin asignar"
    if students:
        # Check the first student's teacher
        # (Assuming all students in a class have same teacher, or we list the first found)
        first_student = students[0]
        if first_student.teacher:
            teacher_name = first_student.teacher.full_name

    # 3. Retrieve ALL cases for the list view
    cases = []
    for s in students:
        surveys = db.query(SurveyResponse).filter(
            SurveyResponse.student_id == s.id
        ).order_by(desc(SurveyResponse.date_submitted)).all()
        cases.extend(surveys)
    
    # Sort cases by date descending
    cases.sort(key=lambda x: x.date_submitted, reverse=True)

    return templates.TemplateResponse("dashboard/classroom_detail.html", {
        "request": request,
        "user": current_user,
        "grade_class": grade_class,
        "cases": cases,
        # New Dashboard Data
        "total_students": total_students,
        "active_alerts_count": active_alerts_count,
        "healthy_percentage": healthy_percentage,
        "teacher_name": teacher_name
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
    
    # ML Prediction
    ml_prob = 0.0
    ml_analysis = "No analysis available"
    try:
        import json
        from app.ml_engine import predict_risk, MODEL_PATH
        import os
        
        if os.path.exists(MODEL_PATH) and survey.raw_answers:
             answers = json.loads(survey.raw_answers)
             ml_prob, ml_analysis = predict_risk(answers)
             ml_prob = round(ml_prob * 100, 1)
    except Exception as e:
        print(f"ML Error: {e}")
        ml_analysis = f"Error generating analysis: {e}"

    # --- AUDIT LOG ---
    from ..models import AuditLog
    client_ip = request.client.host if request.client else "unknown"
    log_entry = AuditLog(
        user_id=current_user.id,
        action="VIEW_CASE_DETAILS",
        target_id=str(survey_id),
        ip_address=client_ip,
        details=f"Viewed case for student {survey.student.internal_code}"
    )
    db.add(log_entry)
    db.commit()
    # -----------------

    return templates.TemplateResponse("dashboard/case_details.html", {
        "request": request, 
        "user": current_user,
        "survey": survey,
        "ml_prob": ml_prob,
        "ml_analysis": ml_analysis
    })

@router.post("/case/{survey_id}/derive")
async def derive_case_to_expert(
    survey_id: int, 
    payload: dict = Body(...), 
    current_user: User = Depends(get_current_user), 
    db: Session = Depends(get_db)
):
    if current_user.role != UserRole.SUPER_ADMIN:
        raise HTTPException(status_code=403, detail="Acceso denegado")
    
    email = payload.get("email")
    if not email:
        raise HTTPException(status_code=400, detail="Email del experto requerido")

    survey = db.query(SurveyResponse).filter(SurveyResponse.id == survey_id).first()
    if not survey:
        raise HTTPException(status_code=404, detail="Caso no encontrado")

    # Save Classification (Feedback)
    classification = payload.get("classification")
    if classification:
        survey.expert_label = classification
        db.commit()

    # SIMULATION LOGS
    print(f"\n======== [DERIVACIÓN A EXPERTO] ========")
    print(f"Enviando detalles del Caso #{survey.id}")
    print(f"Destinatario: {email}")
    print(f"Clasificación Experto: {classification if classification else 'No especificada'}")
    
    # Send Email
    from ..utils.email import send_email
    
    subject = f"Derivación de Caso - Código Alumno: {survey.student.internal_code}"
    
    body = f"""
    <h2>Detalles del Caso Derivado</h2>
    <p><strong>Colegio:</strong> {survey.student.school.name}</p>
    <p><strong>Código Alumno:</strong> {survey.student.internal_code}</p>
    <p><strong>Clase:</strong> {survey.student.grade_class}</p>
    <p><strong>Nivel de Riesgo (Calculado):</strong> {survey.risk_level.value}</p>
    <p><strong>Score:</strong> {survey.calculated_risk_score}</p>
    <hr>
    <h3>Resumen IA:</h3>
    <p>{survey.ai_summary}</p>
    <hr>
    <h3>Clasificación Experto:</h3>
    <p>{classification if classification else 'No especificada'}</p>
    
    <p><em>Este es un mensaje automático del sistema Anti-Bullying App.</em></p>
    """
    
    success = send_email(email, subject, body)
    
    msg = "El caso ha sido derivado correctamente."
    if success:
        msg += " Se ha enviado un correo al experto."
        print("✅ Correo enviado.")
    else:
        msg += " (Nota: Fallo al enviar el correo, verifique credenciales)"
        print("❌ Fallo envio correo.")

    return JSONResponse(content={"message": msg})

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
    # Optimized Status Queries
    # Optimized Status Queries
    from ..models import SurveyResponse, AlertLevel
    
    # NEW STRATEGY: 
    # Instead of fetching ALL risks for ALL history, we only care about the latest status.
    # We can fetch (student_id, risk_level) for top 2 of ALL students.
    # This might be heavy (14k students * 2 rows = 28k rows), but much lighter than loading objects.
    
    # 1. Get all student IDs involved (or just run query on all survey responses)
    # Running window function on ENTIRE table might be heavy but for 14k students it's manageable (ms range in Postgres/SQLite).
    
    # Let's use a modified query that groups by School directly if possible?
    # Window function needs to be per student.
    
    # Get all students with school_id
    # Get all students with school_id and grade_class
    all_students = db.query(Student.id, Student.school_id, Student.grade_class).all()
    
    # Map student_id -> (school_id, grade_class)
    student_info_map = {s.id: (s.school_id, s.grade_class) for s in all_students}
    all_student_ids = list(student_info_map.keys())
    
    # Get latest risks for ALL students
    # Using the helper
    bulk_risks = get_latest_risks_bulk(db, all_student_ids)
    
    # Map: school_id -> set of risks found
    school_risk_map = defaultdict(set)
    # Map: school_id -> classroom_name -> has_critical (bool)
    classroom_critical_map = defaultdict(lambda: defaultdict(bool))
    
    for sid, r_level in bulk_risks:
        info = student_info_map.get(sid)
        if info:
            sch_id, g_class = info
            
            # Add to school risks
            school_risk_map[sch_id].add(r_level)
            
            # Check Critical for Classroom Map
            if r_level == AlertLevel.CRITICAL and g_class:
                classroom_critical_map[sch_id][g_class] = True

    school_status_map = {}
    
    for school in schools:
        status = "green"
        risks = school_risk_map.get(school.id, set())
        
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



@router.get("/api/schools_geojson")
def get_schools_geojson(db: Session = Depends(get_db)):
    from ..models import School, User, UserRole, SurveyResponse, Student
    from fastapi.responses import JSONResponse
    from fastapi.responses import JSONResponse
    from sqlalchemy import or_
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

@router.get("/super_admin/school/{school_id}", response_class=HTMLResponse)
def view_school_detail_as_admin(request: Request, school_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if current_user.role != UserRole.SUPER_ADMIN:
         return templates.TemplateResponse("error.html", {"request": request, "error": "Acceso restringido."})
    
    from ..models import School, Student, SurveyResponse, AlertLevel
    from ..models import School, Student, SurveyResponse, AlertLevel

    school = db.query(School).filter(School.id == school_id).first()
    if not school:
         return templates.TemplateResponse("error.html", {"request": request, "error": "Centro no encontrado."})

    # Reuse logic from school_admin_dashboard
    # 1. Obtener todos los alumnos del centro
    students = db.query(Student).filter(Student.school_id == school.id).all()
    
    # 2. Agrupar por Aula
    classrooms = defaultdict(lambda: {"students": [], "alerts": 0, "status": "green"})
    total_alerts_global = 0
    
    # Pre-fetch recent risks for ALL students in this school
    student_ids = [s.id for s in students]
    bulk_risks = get_latest_risks_bulk(db, student_ids)
    
    student_risk_map = defaultdict(list)
    for sid, r_level in bulk_risks:
        student_risk_map[sid].append(r_level)

    for s in students:
        c_name = s.grade_class if s.grade_class else "Sin Asignar"
        classrooms[c_name]["students"].append(s)
        
        # Check high risk surveys (from optimized map)
        risks = student_risk_map.get(s.id, [])
        high_risk_surveys = 0
        for r in risks:
            if r in [AlertLevel.HIGH, AlertLevel.CRITICAL]:
                high_risk_surveys += 1
        
        classrooms[c_name]["alerts"] += high_risk_surveys
        total_alerts_global += high_risk_surveys

    # 3. Determinar Estado por Aula
    classroom_list = []
    
    for name, data in classrooms.items():
        count = len(data["students"])
        alerts = data["alerts"]
        
        has_critical = False
        for stud in data["students"]:
             stud_risks = student_risk_map.get(stud.id, [])
             if AlertLevel.CRITICAL in stud_risks:
                 has_critical = True
                 break

        # Status Logic
        status_color = "green"
        if has_critical:
            status_color = "red"
        elif alerts > 0:
            status_color = "orange"
            
        classroom_list.append({
            "name": name,
            "student_count": count,
            "alerts_count": alerts,
            "status": status_color,
            "has_critical": has_critical
        })
        
    classroom_list.sort(key=lambda x: x["alerts_count"], reverse=True)

    # Estado Global
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
        "school": school,
        "total_students": len(students),
        "total_alerts": total_alerts_global,
        "school_status": school_status,
        "school_color": school_color,
        "classrooms": classroom_list
    })
