from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from .database import init_db
from dotenv import load_dotenv

# Cargar variables de entorno del .env
load_dotenv()

# Inicializar Base de Datos al arrancar
init_db()

app = FastAPI(title="Anti-Bullying Platform", version="1.0.0")

# Montar estáticos
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Routers
from .routers import forms, auth, dashboard, advice, parents
app.include_router(forms.router)
app.include_router(auth.router)
app.include_router(dashboard.router)
app.include_router(advice.router)
app.include_router(parents.router)

@app.get("/")
def read_root():
    return RedirectResponse(url="/auth/login")
