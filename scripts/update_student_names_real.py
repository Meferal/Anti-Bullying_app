import sys
import os
import random

# Add project root to python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import SessionLocal
from app.models import User, Student

# List of realistic Spanish names
REAL_NAMES = [
    "Alejandro García", "Lucía Martínez", "Mateo López", "Sofía González",
    "Daniel Rodríguez", "Valentina Fernández", "Pablo Pérez", "Martina Sánchez",
    "Hugo Ramírez", "Paula Torres", "Álvaro Ruiz", "Daniela Flores",
    "Adrián Gómez", "Valeria Díaz", "David Vázquez", "Emma Romero",
    "Diego Álvarez", "Carla Jiménez", "Mario Moreno", "Sara Muñoz",
    "Manuel Alonso", "Alba Gutiérrez", "Javier Navarro", "Claudia Gil",
    "Marcos Serrano", "Noa Blanco", "Leo Molina", "Marina Morales",
    "Lucas Ortega", "Julia Delgado", "Enzo Castro", "Irene Ortiz",
    "Jorge Rubió", "Elena Marín", "Izan Sanz", "Carmen Iglesias"
]

def update_students():
    db = SessionLocal()
    try:
        teacher_email = "meferal@hotmail.com"
        print(f"Buscando profesor con email: {teacher_email}")
        
        teacher = db.query(User).filter(User.email == teacher_email).first()
        
        if not teacher:
            print(f"Error: No se encontró al usuario {teacher_email}")
            return

        print(f"Profesor encontrado: {teacher.full_name} (ID: {teacher.id})")
        
        students = db.query(Student).filter(Student.teacher_id == teacher.id).all()
        
        if not students:
            print("No se encontraron alumnos asignados a este profesor.")
            return

        print(f"Se encontraron {len(students)} alumnos. Actualizando nombres...")
        
        used_names = set()
        
        for student in students:
            # Pick a unique name if possible
            available_names = [n for n in REAL_NAMES if n not in used_names]
            if not available_names:
                # Reuse if run out
                new_name = random.choice(REAL_NAMES)
            else:
                new_name = random.choice(available_names)
                used_names.add(new_name)
            
            old_name = student.name
            student.name = new_name
            print(f"Alumno {student.internal_code}: {old_name} -> {new_name}")
            
        db.commit()
        print("✅ Base de datos actualizada correctamente.")
        
    except Exception as e:
        print(f"Error: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    update_students()
