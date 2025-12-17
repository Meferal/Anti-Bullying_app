# Herramientas de Desarrollo (Dev Utils)

Esta carpeta contiene scripts auxiliares utilizados **únicamente durante el desarrollo y pruebas** de la aplicación.
**NO** deben utilizarse en un entorno de producción real, ya que generan datos ficticios o realizan modificaciones masivas en la base de datos con fines de testeo.

**⚠️ Importante:** Todos los scripts deben ejecutarse desde la **raíz del proyecto** para que las importaciones funcionen.
Ejemplo: `python dev_utils/generate_full_data.py`

---

## 📂 Clasificación de Scripts

### 1. Generación de Datos (Seeding & Demo)
Scripts para poblar la base de datos con información ficticia para pruebas de carga o demostraciones.

*   **`create_demo_users.py`**: Crea usuarios básicos de prueba (Profesor, Director, Super Admin) con contraseñas conocidas.
*   **`generate_full_data.py`**: Script maestro para generar una población escolar masiva y realista (colegios, clases, alumnos, encuestas).
*   **`generate_history.py`**: Genera un histórico semanal de encuestas retroactivas (ej. desde septiembre) para simular la evolución temporal de los casos.
*   **`populate_full_classes.py`**: Rellena clases existentes con 20-25 alumnos ficticios y genera respuestas de encuesta para ellos.
*   **`seed_data.py`**: Semilla básica de datos para desarrollo inicial.
*   **`seed_large_db.py`**: Generación de volúmenes muy altos de datos para pruebas de estrés.
*   **`seed_parent_surveys.py`**: Genera respuestas ficticias de familias para probar el módulo de padres.
*   **`create_custom_scenario.py`**: Crea un escenario específico controlado con casos de acoso predefinidos para demos guiadas.
*   **`create_demo_parent.py`**: Crea un usuario padre específico y lo vincula a un alumno.
*   **`generate_reports_from_excel.py`**: Genera reportes masivos utilizando un Excel como fuente de nombres o estructura.

### 2. Limpieza y Mantenimiento (Cleanup)
Scripts para eliminar datos y resetear el estado de la aplicación.

*   **`delete_fake_data.py`**: Elimina todos los datos generados como "ficticios", ideal para limpiar la BBDD después de pruebas.
*   **`cleanup_old_records.py`**: Borra registros de encuestas antiguos (ej. de meses anteriores) para liberar espacio.
*   **`cleanup_group_c.py`**: Script específico para borrar alumnos y datos del grupo "C" (usado en una demo anterior).

### 3. Debugging y Diagnóstico
Herramientas para inspeccionar el estado interno de la aplicación y buscar errores.

*   **`debug_env.py`**: Verifica que el archivo `.env` se lea correctamente.
*   **`debug_map_api.py`** / **`check_map_data.py`** / **`check_map_status.py`**: Diagnostican problemas con la visualización del mapa de centros y los colores de alerta.
*   **`debug_relationships.py`**: Comprueba la integridad de las relaciones SQLAlchemy (ej. ¿tienen todos los alumnos un profesor asignado?).
*   **`check_school_population.py`**: Muestra estadísticas de alumnos por centro.
*   **`check_schema.py`** / **`check_columns.py`**: Verifican la estructura de las tablas de la base de datos.
*   **`fix_db_schema.py`**: Script antiguo para correcciones manuales de esquema (BBDD).
*   **`test_email_debug.py`**: Prueba el envío de correos electrónicos simulados.
*   **`inspect_excel.py`** / **`inspect_valencia_xls.py`** / **`read_docx.py`**: Scripts para inspeccionar el contenido de archivos externos subidos o de referencia.

### 4. Tests Ad-hoc
Pruebas manuales de funcionalidades específicas.

*   **`test_login.py`**: Simula el proceso de login.
*   **`test_agent.py`**: Prueba el agente de IA conversacional.
*   **`test_db_integration.py`**: Verifica la conexión y operaciones básicas con la base de datos.
*   **`test_password_policy.py`**: Comprueba las reglas de validación de contraseñas.
*   **`retrain_model.py`**: Script simple para lanzar un re-entrenamiento manual del modelo de IA (si aplica).
*   **`add_class_observation.py`**: Script puntual para añadir observaciones a una clase.

---

## 🚫 Gitignore
Esta carpeta (`dev_utils/`) está incluida en `.gitignore`. Su contenido es SOLO LOCAL y no se subirá al repositorio.
