from fastapi import APIRouter, Depends, HTTPException, status, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import User, Student, School, ParentStudentLink, UserRole
from ..schemas import StudentCreate
from ..security import get_current_user

router = APIRouter(prefix="/parents", tags=["parents"])
templates = Jinja2Templates(directory="app/templates")

@router.get("/dashboard", response_class=HTMLResponse)
def parent_dashboard(request: Request, current_user: User = Depends(get_current_user)):
    # Verificar rol
    if current_user.role != UserRole.PARENT:
         return templates.TemplateResponse("error.html", {"request": request, "error": "Acceso solo para padres."})

    return templates.TemplateResponse("parents/dashboard.html", {
        "request": request,
        "user": current_user,
        "children": current_user.children
    })

@router.post("/add_child")
def add_child_to_parent(
    name: str = Form(...),
    age: int = Form(...),
    grade: str = Form(None), # Clase opcional
    teacher_code: str = Form(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    teacher = None
    school_id = None
    msg = "Alumno registrado correctamente."
    
    # 1. Si hay código, buscamos Profesor
    if teacher_code:
        teacher = db.query(User).filter(User.teacher_code == teacher_code).first()
        if not teacher:
            return RedirectResponse(
                url=f"/parents/add_child_form?error=Codigo+de+profesor+invalido.+Intentalo+de+nuevo+o+dejalo+en+blanco.", 
                status_code=status.HTTP_303_SEE_OTHER
            )
        school_id = teacher.school_id
        msg = "Alumno registrado y vinculado al profesor correctamente."
    else:
        msg = "Alumno registrado SIN vincular. Los datos se guardarán localmente."

    # 2. Crear Alumno
    import uuid
    internal_code = f"{name[:3].upper()}-{uuid.uuid4().hex[:4]}"
    
    new_student = Student(
        internal_code=internal_code,
        name=name,
        age=age,
        grade_class=grade if grade else "Sin asignar",
        school_id=school_id, 
        teacher_id=teacher.id if teacher else None 
    )
    db.add(new_student)
    db.commit()
    
    # 3. Asociar al Padre (Current User)
    current_user.children.append(new_student)
    db.commit()
        
    return RedirectResponse(
        url=f"/parents/dashboard?message={msg}", 
        status_code=status.HTTP_303_SEE_OTHER
    )

@router.get("/add_child_form", response_class=HTMLResponse)
def add_child_form(request: Request, current_user: User = Depends(get_current_user)):
    return templates.TemplateResponse("parents/add_child.html", {"request": request, "user": current_user})

@router.get("/edit_child_form", response_class=HTMLResponse)
def edit_child_form_page(request: Request, student_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    # Verificar propiedad
    student = db.query(Student).filter(Student.id == student_id).first()
    if not student or student not in current_user.children:
         raise HTTPException(status_code=404, detail="Student not found or unauthorized")
         
    return templates.TemplateResponse("parents/edit_child.html", {"request": request, "user": current_user, "student": student})

@router.post("/edit_child")
async def edit_child_action(
    request: Request,
    student_id: int = Form(...),
    age: int = Form(...),
    grade: str = Form(None),
    teacher_code: str = Form(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    student = db.query(Student).filter(Student.id == student_id).first()
    if not student or student not in current_user.children:
         raise HTTPException(status_code=404, detail="Student not found or unauthorized")
    
    # Update Name explicitly if desired, but let's handle it better with Form param if possible,
    # but I switched to Request to avoiding signature clash? No, I can add `name: str = Form(...)`.
    # Let's pivot back to signature for cleaner code.
    form = await request.form()
    if 'name' in form:
        student.name = form['name']
    
    # Update básico
    student.age = age
    if grade:
        student.grade_class = grade
    
    # Update name if provided in form (need to add to function signature first)
    if 'name' in await request.form():
        student.name = (await request.form())['name']
    
    msg = "Datos actualizados correctamente."
    
    # Update Teacher si se da código
    if teacher_code:
        teacher = db.query(User).filter(User.teacher_code == teacher_code).first()
        if not teacher:
             return templates.TemplateResponse("parents/edit_child.html", {
                 "request": {}, "user": current_user, "student": student, "error": "Código de profesor inválido"
             })
        
        student.teacher_id = teacher.id
        student.school_id = teacher.school_id
        msg = "Alumno vinculado al nuevo profesor correctamente."
        
    db.commit()
    
    return RedirectResponse(
        url=f"/parents/dashboard?message={msg}", 
        status_code=status.HTTP_303_SEE_OTHER
    )
