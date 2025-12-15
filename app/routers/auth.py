from fastapi import APIRouter, Depends, HTTPException, status, Request, Form
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from datetime import timedelta
from ..database import get_db
from ..models import User
from ..security import verify_password, create_access_token, ACCESS_TOKEN_EXPIRE_MINUTES, get_current_user

router = APIRouter(prefix="/auth", tags=["auth"])
templates = Jinja2Templates(directory="app/templates")

@router.get("/login", response_class=HTMLResponse)
def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@router.post("/login")
async def login_for_access_token(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.email == form_data.username).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        # Si es formulario web HTMX, podríamos devolver un error parcial
        # Por simplicidad ahora, lanzamos 401 standard
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email, "role": user.role.value}, expires_delta=access_token_expires
    )
    
    # Lógica de Redirección según Rol
    # Lógica de Redirección según Rol
    redirect_url = "/parents/dashboard"
    if user.role.value == "teacher":
        redirect_url = "/dashboard/teacher"
    elif user.role.value == "school_admin":
        redirect_url = "/dashboard/school_admin"
    elif user.role.value == "super_admin":
        redirect_url = "/dashboard/super_admin"

    # Si la solicitud espera HTML (Browser Submit)
    if "text/html" in request.headers.get("accept", ""):
        response = RedirectResponse(url=redirect_url, status_code=status.HTTP_303_SEE_OTHER)
        response.set_cookie(key="access_token", value=access_token, httponly=True)
        return response

    # Respuesta JSON para SPA/Mobile
    response = JSONResponse(content={"access_token": access_token, "token_type": "bearer", "redirect_url": redirect_url})
    response.set_cookie(key="access_token", value=access_token, httponly=True)
    return response

@router.get("/register", response_class=HTMLResponse)
def register_page(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})

@router.post("/register")
def register_user(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    confirm_password: str = Form(...), # Nuevo campo
    full_name: str = Form(...),
    role: str = Form(...),
    center_code: str = Form(None),
    gdpr_consent: str = Form(None), # Checkbox
    db: Session = Depends(get_db)
):
    from ..models import UserRole
    from ..security import get_password_hash, validate_password_strength

    # 1. Validar Consentimiento GDPR
    if not gdpr_consent:
         return templates.TemplateResponse("register.html", {
             "request": request, "error": "Debes aceptar la Política de Privacidad para registrarte."
         })

    # 2. Validar coincidencia de passwords
    if password != confirm_password:
         return templates.TemplateResponse("register.html", {
             "request": request, "error": "Las contraseñas no coinciden."
         })

    # 2. Validar password strength
    try:
        validate_password_strength(password)
    except HTTPException as e:
         return templates.TemplateResponse("register.html", {"request": request, "error": e.detail})

    # 2. Check si existe
    existing_user = db.query(User).filter(User.email == email).first()
    if existing_user:
        if existing_user.role == UserRole.TEACHER and role == "parent":
            error_msg = "Este correo ya está registrado como Profesor. Por favor, usa otra dirección para la cuenta de Padre/Tutor."
        elif existing_user.role == UserRole.PARENT and role == "teacher":
            error_msg = "Este correo ya está registrado como Padre. Por favor, usa otra dirección para la cuenta de Profesor."
        else:
            error_msg = "Este correo electrónico ya está registrado en el sistema."
            
        return templates.TemplateResponse("register.html", {"request": request, "error": error_msg})

        return templates.TemplateResponse("register.html", {"request": request, "error": error_msg})

    # 3. Validation School Code
    school_id = None
    
    # Director obligatoriamente necesita codigo
    if role == "school_admin":
        if not center_code:
            return templates.TemplateResponse("register.html", {
                 "request": request, "error": "El código de centro es obligatorio para registrarse como Director."
             })
             
    if (role == "teacher" or role == "school_admin") and center_code:
        from ..models import School
        school = db.query(School).filter(School.center_code == center_code).first()
        if not school:
             return templates.TemplateResponse("register.html", {
                 "request": request, "error": f"No se encontró ningún centro con el código '{center_code}'"
             })
        school_id = school.id
        
        # Si es Director, verificar que no haya ya uno registrado para este cole? (Opcional, pero sensato)
        # Por ahora permitimos multiples directores por simplicidad o equipos directivos.

    # 3b. Validar Clave Conselleria
    if role == "super_admin":
        if center_code != "VALENCIA":
             return templates.TemplateResponse("register.html", {
                 "request": request, "error": "La clave de acceso para Conselleria es incorrecta."
             })

    # 4. Generar código si es profesor (Personal)
    teacher_code = None
    if role == "teacher":
        import random, string
        suffix = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))
        teacher_code = f"PROF-{suffix}"

        suffix = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))
        teacher_code = f"PROF-{suffix}"

    user_role = UserRole.PARENT
    if role == "teacher":
        user_role = UserRole.TEACHER
    elif role == "school_admin":
        user_role = UserRole.SCHOOL_ADMIN
    elif role == "super_admin":
        user_role = UserRole.SUPER_ADMIN

    new_user = User(
        email=email,
        hashed_password=get_password_hash(password),
        full_name=full_name,
        role=user_role,
        teacher_code=teacher_code,
        school_id=school_id 
    )
    db.add(new_user)
    db.commit()

    # AUTO LOGIN
    from ..security import create_access_token
    access_token = create_access_token(
        data={"sub": new_user.email, "role": new_user.role.value}
    )
    
    access_token = create_access_token(
        data={"sub": new_user.email, "role": new_user.role.value}
    )
    
    if user_role == UserRole.TEACHER:
        redirect_url = "/dashboard/teacher"
    elif user_role == UserRole.SCHOOL_ADMIN:
        redirect_url = "/dashboard/school_admin"
    elif user_role == UserRole.SUPER_ADMIN:
        redirect_url = "/dashboard/super_admin"
    else:
        redirect_url = "/parents/dashboard"
    
    response = RedirectResponse(url=redirect_url, status_code=status.HTTP_303_SEE_OTHER)
    response.set_cookie(key="access_token", value=access_token, httponly=True)
    return response

@router.get("/privacy-policy", response_class=HTMLResponse)
def privacy_policy_page(request: Request):
    return templates.TemplateResponse("privacy_policy.html", {"request": request})

@router.get("/forgot-password", response_class=HTMLResponse)
def forgot_password_page(request: Request):
    return templates.TemplateResponse("forgot_password.html", {"request": request})

@router.post("/forgot-password")
async def forgot_password_action(email: str = Form(...), db: Session = Depends(get_db)):
    # 1. Buscar Usuario
    user = db.query(User).filter(User.email == email).first()
    
    # 2. Simular envío de correo
    if user:
        import uuid
        # Generar token real y guardar en BD
        recovery_token = f"REC-{uuid.uuid4().hex[:6].upper()}"
        user.recovery_token = recovery_token
        db.commit()

        print(f"==========================================")
        print(f"[SIMULACIÓN EMAIL] Enviando a: {email}")
        print(f"Asunto: Recuperación de Contraseña")
        print(f"Hola {user.full_name},")
        print(f"Tu clave de recuperación es: {recovery_token}")
        print(f"Introduce esta clave en: http://localhost:8000/auth/reset-password")
        print(f"==========================================")
    
    # Redirigir a pantalla de "Introduce tu código" (Reset Password)
    # Para mejorar UX, redirigimos directos al formulario de reset
    return RedirectResponse(url="/auth/reset-password", status_code=status.HTTP_303_SEE_OTHER)

@router.get("/reset-password", response_class=HTMLResponse)
def reset_password_page(request: Request):
    return templates.TemplateResponse("reset_password.html", {"request": request})

@router.post("/reset-password")
def reset_password_action(
    request: Request,
    email: str = Form(...),
    token: str = Form(...),
    new_password: str = Form(...),
    db: Session = Depends(get_db)
):
    from ..security import get_password_hash, validate_password_strength

    # 1. Validar Usuario y Token
    user = db.query(User).filter(User.email == email).first()
    if not user or user.recovery_token != token:
        return templates.TemplateResponse("reset_password.html", {
            "request": request, 
            "error": "Email o código incorrecto."
        })

    # 2. Validar password strength
    try:
        validate_password_strength(new_password)
    except HTTPException as e:
        return templates.TemplateResponse("reset_password.html", {
            "request": request, 
            "error": e.detail
        })

    # 3. Actualizar Password y borrar token
    user.hashed_password = get_password_hash(new_password)
    user.recovery_token = None # Quemar token
    db.commit()

    # AUTO LOGIN
    from ..security import create_access_token
    from ..models import UserRole # Asegurar que UserRole está disponible
    
    access_token = create_access_token(
        data={"sub": user.email, "role": user.role.value}
    )
    
    redirect_url = "/dashboard/teacher" if user.role == UserRole.TEACHER or user.role == UserRole.SCHOOL_ADMIN else "/parents/dashboard"
    
    response = RedirectResponse(url=redirect_url, status_code=status.HTTP_303_SEE_OTHER)
    response.set_cookie(key="access_token", value=access_token, httponly=True)
    return response

@router.get("/logout")
def logout():
    response = RedirectResponse(url="/auth/login", status_code=status.HTTP_303_SEE_OTHER)
    response.delete_cookie("access_token")
    return response

@router.get("/edit-profile", response_class=HTMLResponse)
def edit_profile_page(request: Request, current_user: User = Depends(get_current_user)):
    return templates.TemplateResponse("edit_profile.html", {"request": request, "user": current_user})

@router.post("/edit-profile")
def edit_profile_action(
    request: Request,
    full_name: str = Form(...),
    center_code: str = Form(None),
    new_password: str = Form(None),
    confirm_new_password: str = Form(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    from ..security import get_password_hash, validate_password_strength

    message = None
    error = None

    # 1. Actualizar Nombre
    if full_name:
        current_user.full_name = full_name

    # 1b. Actualizar Colegio (Si es profesor y envía código)
    if center_code:
        from ..models import School
        # Buscar colegio por código
        school = db.query(School).filter(School.center_code == center_code).first()
        if school:
            current_user.school_id = school.id
            if not message: message = "Perfil actualizado"
            message += " y vinculado al centro " + school.name + "."
        else:
             return templates.TemplateResponse("edit_profile.html", {
                 "request": request, "user": current_user, "error": f"No se encontró ningún centro con el código '{center_code}'"
             })

    # 2. Actualizar Password (si se provee)
    if new_password:
        if new_password != confirm_new_password:
             return templates.TemplateResponse("edit_profile.html", {
                 "request": request, "user": current_user, "error": "Las contraseñas no coinciden."
             })
        
        try:
            validate_password_strength(new_password)
            current_user.hashed_password = get_password_hash(new_password)
            message = "Perfil y contraseña actualizados correctamente."
        except HTTPException as e:
             return templates.TemplateResponse("edit_profile.html", {
                 "request": request, "user": current_user, "error": e.detail
             })
    else:
        message = "Perfil actualizado correctamente."

    db.commit()
    db.refresh(current_user)

    return templates.TemplateResponse("edit_profile.html", {
        "request": request, "user": current_user, "message": message
    })

