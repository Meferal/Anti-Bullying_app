# Scripts de Administración y Despliegue

Esta carpeta contiene scripts esenciales para la puesta en marcha, mantenimiento y administración de la aplicación R.A.D.A.R. en entornos de producción.

**Nota:** Todos los scripts deben ejecutarse desde la **raíz del proyecto** para que las importaciones de Python funcionen correctamente.

---

## 🛠️ Listado de Scripts

### 1. Inicialización de Usuarios
*   **`create_super_admin.py`**
    *   **Función:** Crea una cuenta de usuario con rol `SUPER_ADMIN` (Consellería). Es necesario ejecutarlo al menos una vez tras una instalación limpia para tener acceso total al sistema.
    *   **Uso:** `python scripts/create_super_admin.py`

### 2. Gestión de Centros (Generalitat)
*   **`import_schools_from_xls.py`**
    *   **Función:** Importa masivamente centros educativos desde un archivo Excel oficial (ej. listado GVA). Crea las cuentas de `SCHOOL_ADMIN` asociadas automáticamente y genera las contraseñas iniciales.
    *   **Uso:** `python scripts/import_schools_from_xls.py` (requiere configurar la ruta del Excel en el código o renombrarlo).
*   **`import_schools.py`**
    *   **Función:** Versión alternativa para importar centros desde fuentes de datos estructuradas (JSON/CSV) si no se usa el formato Excel específico.
    *   **Uso:** `python scripts/import_schools.py`

### 3. Mantenimiento de Base de Datos
*   **`update_db_schema.py`**
    *   **Función:** Realiza migraciones ligeras de la base de datos. Si se han añadido nuevas tablas o columnas en el código (`models.py`), este script intenta actualizar la base de datos existente sin borrar los datos.
    *   **Uso:** `python scripts/update_db_schema.py`

### 4. Consultas de Utilidad
*   **`get_school_codes.py`**
    *   **Función:** Muestra en consola un listado rápido de los colegios importados, sus IDs y, lo más importante, sus **códigos de centro** (necesarios para el registro de profesores y alumnos).
    *   **Uso:** `python scripts/get_school_codes.py`

---

## ⚠️ Advertencia
*   Si buscas scripts para generar datos de prueba, usuarios falsos o debugging, revisa la carpeta **`dev_utils/`**.
*   Asegúrate de tener el entorno virtual activado antes de ejecutar estos comandos.
