from fastapi import APIRouter, HTTPException, Request, Depends
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from ..agents.rag_expert import rag_system
from ..security import get_current_user, User
from ..models import UserRole, ChatMessage
from ..database import get_db

router = APIRouter(prefix="/advice", tags=["advice"])
templates = Jinja2Templates(directory="app/templates")

@router.get("/chat", response_class=HTMLResponse)
def chat_page(request: Request, current_user: User = Depends(get_current_user)):
    return templates.TemplateResponse("chat.html", {
        "request": request,
        "user": current_user
    })

@router.get("/teacher", response_class=HTMLResponse)
def teacher_advice_page(request: Request, current_user: User = Depends(get_current_user)):
    # Verify role (optional redundancy but good for security)
    if current_user.role not in [UserRole.TEACHER, UserRole.SCHOOL_ADMIN]:
        return templates.TemplateResponse("error.html", {"request": request, "error": "Acceso restringido"})
    return templates.TemplateResponse("chat.html", {"request": request, "user": current_user, "mode": "Teacher"})

@router.get("/parent", response_class=HTMLResponse)
def parent_advice_page(request: Request, current_user: User = Depends(get_current_user)):
    if current_user.role != UserRole.PARENT:
         return templates.TemplateResponse("error.html", {"request": request, "error": "Acceso restringido"})
    return templates.TemplateResponse("chat.html", {"request": request, "user": current_user, "mode": "Parent"})

@router.get("/widget", response_class=HTMLResponse)
def widget_page(request: Request, current_user: User = Depends(get_current_user)):
    return templates.TemplateResponse("chat_widget.html", {"request": request, "user": current_user})

@router.get("/ask")
def ask_expert(
    query: str, 
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Endpoint para preguntar al RAG.
    Rol determinado automáticamente por el login.
    Guarda historial y usa contexto previo.
    """
    if not query:
        raise HTTPException(status_code=400, detail="Query vacía")
    
    # 1. Determinar Rol RAG
    rag_role = "parents"
    if current_user.role in [UserRole.TEACHER, UserRole.SCHOOL_ADMIN, UserRole.SUPER_ADMIN]:
        rag_role = "teachers"

    # 2. Recuperar Historial (Últimos 5 mensajes)
    last_messages = db.query(ChatMessage).filter(
        ChatMessage.user_id == current_user.id
    ).order_by(ChatMessage.timestamp.desc()).limit(5).all()
    
    # Formatear para el prompt (revertir orden para cronología)
    history_text = "\n".join([f"{msg.role.capitalize()}: {msg.content}" for msg in reversed(last_messages)])

    # 3. Consultar RAG + Historial
    response_text = rag_system.get_advice(query, rag_role, history_text)

    # 4. Guardar Conversación
    # Msj Usuario
    user_msg = ChatMessage(user_id=current_user.id, role="user", content=query)
    db.add(user_msg)
    
    # Msj IA
    ai_msg = ChatMessage(
        user_id=current_user.id, 
        role="assistant", 
        content=response_text,
        rag_context_used=rag_role
    )
    db.add(ai_msg)
    
    db.commit()

    return {"response": response_text, "role_used": rag_role}
