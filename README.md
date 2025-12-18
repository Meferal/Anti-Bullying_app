<div align="center">

![logo](./documents/img/Logo_R.A.D.A.R..png)

# Anti-Bullying App - Proyecto de Detección y Prevención
# R.A.D.A.R. (Red de Alerta y Detección de Acoso Relacional)

<!-- Tech Stack Badges -->
![Python](https://img.shields.io/badge/Python-3.11-3776AB?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-009688?logo=fastapi&logoColor=white)
![Pydantic](https://img.shields.io/badge/Pydantic-E92063?logo=pydantic&logoColor=white)
![Uvicorn](https://img.shields.io/badge/Uvicorn-2C2C2C?logo=uvicorn&logoColor=white)
![LangChain](https://img.shields.io/badge/LangChain-1C3C3C?logo=langchain&logoColor=white)
![OpenAI](https://img.shields.io/badge/OpenAI-412991?logo=openai&logoColor=white)
![Scikit-Learn](https://img.shields.io/badge/scikit--learn-F7931E?logo=scikit-learn&logoColor=white)
![Pandas](https://img.shields.io/badge/Pandas-150458?logo=pandas&logoColor=white)
![NumPy](https://img.shields.io/badge/NumPy-013243?logo=numpy&logoColor=white)
![SHAP](https://img.shields.io/badge/SHAP-Model%20Explainer-blue)
![SQLite](https://img.shields.io/badge/SQLite-003B57?logo=sqlite&logoColor=white)
![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-D71F00?logo=sqlalchemy&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-2496ED?logo=docker&logoColor=white)
![SonarQube](https://img.shields.io/badge/SonarQube-4E9BCD?logo=sonarqube&logoColor=white)
![Nginx](https://img.shields.io/badge/Nginx-009639?logo=nginx&logoColor=white)
![Ubuntu](https://img.shields.io/badge/Ubuntu-E95420?logo=ubuntu&logoColor=white)
![Burp Suite](https://img.shields.io/badge/Burp%20Suite-FF6633?logo=burpsuite&logoColor=white)
![HTML5](https://img.shields.io/badge/HTML5-E34F26?logo=html5&logoColor=white)
![CSS3](https://img.shields.io/badge/CSS3-1572B6?logo=css3&logoColor=white)
![Jinja2](https://img.shields.io/badge/Jinja2-B41717?logo=jinja&logoColor=white)

<!-- Custom/Generic Badges for Tools without standard SimpleIcons -->
![pfSense](https://img.shields.io/badge/pfSense-Firewall-black?logo=pfsense&logoColor=white)
![ModSecurity](https://img.shields.io/badge/ModSecurity-WAF-blue)
![Wazuh](https://img.shields.io/badge/Wazuh-SIEM-blueviolet)
![Nessus](https://img.shields.io/badge/Nessus-Vulnerability%20Scan-green)

<br>

<!-- Deployment & Docker Hub Links -->
[![Docker Hub](https://img.shields.io/badge/Docker%20Hub-Descargar%20Imágenes-2496ED?logo=docker&logoColor=white)](https://hub.docker.com/repository/docker/meferal/anti-bullying-app/general)
[![Render](https://img.shields.io/badge/Render-Deployed-46E3B7?logo=render&logoColor=white)](https://anti-bullying-app.onrender.com)

<br>

<!-- Documentation Links -->
[Ver Documentación](http://localhost:8000/docs) • [Reportar Bug](https://github.com/Meferal/Anti-Bullying_app/issues/new?labels=bug) • [Solicitar Feature](https://github.com/Meferal/Anti-Bullying_app/issues/new?labels=enhancement)

</div>

---

## 📋 Descripción Completa

Este proyecto es una aplicación web integral diseñada para la **detección, prevención y gestión de casos de bullying** en entornos escolares. Utiliza técnicas avanzadas de **Data Science** y **Machine Learning** para analizar encuestas y comportamientos, permitiendo a los administradores escolares y profesores identificar situaciones de riesgo de manera temprana.

La plataforma ofrece diferentes roles (Super Admin, Admin de Escuela, Profesor, Padre/Madre) con funcionalidades adaptadas, incluyendo dashboards interactivos, mapas de calor, asistentes de IA para orientación psicopedagógica y sistemas de reporte seguro.

## ✨ Características Principales

*   **Detección Temprana con ML:** Modelo predictivo entrenado para identificar patrones de acoso escolar.
*   **Gestión Multi-Rol:** Paneles específicos para Conselleria, Colegios, Profesores y Familias.
*   **Arquitectura Multi-Agente:** Sistema inteligente compuesto por múltiples agentes especializados que colaboran para ofrecer respuestas precisas y contextualizadas.
*   **Asistente IA:** Chatbot integrado que utiliza estos agentes para ofrecer consejos y pautas de actuación a padres y profesores.
*   **Mapas de Calor:** Visualización geoespacial de incidencias (ficticias para demo) a nivel global.
*   **Seguridad Avanzada:** Protección robusta contra vulnerabilidades web y gestión segura de sesiones y contraseñas.
*   **Diseño Responsive:** Interfaz adaptada a dispositivos móviles con soporte para modo apaisado.

## 🛠️ Tech Stack

### Data Science & Backend
*   **Python 3.11**: Lenguaje principal.
*   **FastAPI / Flask**: Frameworks para la API y servidor web.
*   **Scikit-learn**: Entrenamiento y uso de modelos de ML.
*   **Pandas / NumPy**: Procesamiento de datos.
*   **SQLite / SQLAlchemy**: Gestión de base de datos.
*   **Docker**: Contenerización de la aplicación.

### Ciberseguridad
Se han implementado y utilizado las siguientes herramientas para garantizar la seguridad del entorno:
*   **SonarQube**: Análisis estático y sanitización de código.
*   **pfSense**: Firewall para protección LAN y defensa WAN.
*   **ModSecurity**: WAF (Web Application Firewall) para protección contra ataques web (OWASP).
*   **Wazuh**: SIEM para la gestión de eventos de seguridad y alertas (SOC).
*   **Ubuntu Server + Nginx**: Servidor web seguro y proxy inverso.
*   **Burp Suite**: Pruebas de pentesting y análisis de vulnerabilidades web.
*   **Nessus**: Escaneo de vulnerabilidades en la infraestructura.

## 📂 Estructura del Proyecto

```text
Anti-Bullying_app/
├── app/
│   ├── agents/          # Agentes de IA y Lógica de Predicción
│   ├── routers/         # Rutas de la API (Endpoints)
│   ├── static/          # Archivos estáticos (CSS, JS, Imágenes)
│   ├── templates/       # Plantillas HTML (Jinja2)
│   ├── utils/           # Utilidades y funciones auxiliares
│   ├── main.py          # Punto de entrada de la aplicación
│   ├── models.py        # Modelos de Base de Datos (ORM)
│   ├── schemas.py       # Esquemas Pydantic para validación
│   ├── security.py      # Lógica de autenticación y seguridad
│   ├── ml_engine.py     # Motor de Machine Learning
│   └── database.py      # Configuración de la DB
├── documents/           # Base de conocimiento para RAG (Retrieval Augmented Generation)
│   ├── parents/         # Documentación para el asistente de familias
│   └── teachers/        # Documentación para el asistente de docentes
├── Dockerfile           # Definición de la imagen Docker
├── docker-compose.yml   # Orquestación de servicios
├── dev_utils/           # Herramientas de Desarrollo y Testing (Local - No Prod)
├── scripts/             # Scripts de Administración y Despliegue (Prod)
└── requirements.txt     # Dependencias del proyecto
```

## ⚙️ Configuración del Entorno (Variables de Entorno)

Para que la aplicación funcione correctamente en local, es **obligatorio** crear un archivo `.env` en la raíz del proyecto. Este archivo contiene credenciales y configuraciones sensibles.

Crea un archivo llamado `.env` y añade las siguientes variables:

```bash
# Seguridad de la Aplicación
SECRET_KEY="tu_secret_key_generada_aleatoriamente"
ENVIRONMENT="development" # Use 'production' para despliegue real

# Configuración de Correo (Gmail SMTP - Para recuperación de claves)
EMAIL_USER="tucorreo@gmail.com"
EMAIL_PASSWORD="tu_contraseña_de_aplicacion_google"

# Inteligencia Artificial (OpenAI API)
OPENAI_API_KEY="sk-..."
```

> [!WARNING]
> Nunca subas el archivo `.env` al repositorio. Asegúrate de que está incluido en el `.gitignore`.

## 🚀 Guía de Inicio Rápido (Local)

1.  **Clonar el repositorio:**
    ```bash
    git clone https://github.com/Meferal/Anti-Bullying_app.git
    cd Anti-Bullying_app
    ```

2.  **Instalar dependencias:**
    ```bash
    pip install -r requirements.txt
    ```

3.  **Ejecutar la aplicación:**
    ```bash
    python -m app.main
    # O usando uvicorn directamente:
    # uvicorn app.main:app --reload
    ```
4.  **Acceder:** Abre tu navegador en `http://localhost:8000`.

## 🐳 Guía de Uso Rápido con Docker Hub

Para desplegar la aplicación utilizando la imagen pre-construida:

```bash
# Descargar la imagen
docker pull meferal/anti-bullying-app:latest

# Ejecutar el contenedor
docker run -d -p 8000:8000 --name anti-bullying-app meferal/anti-bullying-app:latest
```

Accede a la aplicación en `http://localhost:8000`.

## 📚 Documentación de la API

La documentación interactiva (Swagger UI) está habilitada por defecto y accesible en:
*   **Swagger UI:** `http://localhost:8000/docs`
*   **ReDoc:** `http://localhost:8000/redoc`

Aquí podrás probar los endpoints de autenticación, gestión de usuarios y predicción de modelos directamente.

## ☁️ Guía de Despliegue Cloud

La aplicación está preparada para desplegarse en **Render** u otras plataformas PaaS compatibles con Docker.

1.  Conecta tu repositorio de GitHub a Render.
2.  Selecciona "New Web Service".
3.  Elige "Docker" como entorno de ejecución.
4.  Render detectará automáticamente el `Dockerfile`.
5.  Configura las variables de entorno necesarias (si las hubiera).
6.  Despliega.

---

## 👥 Autores

### Data Science
*   **Álvaro Medina Fernández** [GitHub](https://github.com/Meferal) | [LinkedIn](http://www.linkedin.com/in/álvaro-medinafernández)
*   **Juan Arturo Puig Ontiveros** [GitHub](https://github.com/Arturopuig2) | [LinkedIn](https://www.linkedin.com/in/arturopuigontiveros/)
*   **Reiner Fuentes Ferrada** [GitHub](https://github.com/Rei-Fuentes) | [LinkedIn](https://www.linkedin.com/in/reiner-psicologo/)
*   **Cindy Tatiana Marin Espinosa** [GitHub](https://github.com/citmaes17) | [LinkedIn](https://www.linkedin.com/in/cindy-marine/)

### Ciberseguridad
*   **Laura Bea del Olmo** [LinkedIn](https://www.linkedin.com/in/laurabeadelolmo/)
*   **Raniero Julio Del Federico** [LinkedIn](https://www.linkedin.com/in/ranierodf/)
*   **David Laencina López** [LinkedIn](https://www.linkedin.com/in/david-laencina-l%C3%B3pez-0372ba238/)
*   **Sebastian Correa** [LinkedIn](https://www.linkedin.com/in/sebastian-correa-99b25a342/?trk=contact-info)
