from app.database import SessionLocal
from app.models import User, Student, UserRole, ParentStudentLink, School
from app.security import get_password_hash

db = SessionLocal()

# 1. Get School/Student
# Using the same school as the teacher example: 46003640
school_code = "46003640"
school = db.query(School).filter(School.center_code == school_code).first()

if not school:
    print(f"School {school_code} not found. Picking first active one.")
    school = db.query(School).join(Student).first()

student = db.query(Student).filter(Student.school_id == school.id).first()

if not student:
    print("No students found.")
    exit()

print(f"Linking parent to Student ID: {student.id} ({student.internal_code}) in School: {school.name}")

# 2. Create Parent
parent_email = "padre_demo@demo.com"
parent = db.query(User).filter(User.email == parent_email).first()

if not parent:
    parent = User(
        email=parent_email,
        full_name="Padre Ejemplo",
        hashed_password=get_password_hash("123456"),
        role=UserRole.PARENT,
        school_id=None # Parents don't belong to a school directly in this model usually, or do they? Model says school_id is nullable.
    )
    db.add(parent)
    db.commit()
    db.refresh(parent)
    print("Parent user created.")

# 3. Link
link = db.query(ParentStudentLink).filter_by(parent_id=parent.id, student_id=student.id).first()
if not link:
    link = ParentStudentLink(parent_id=parent.id, student_id=student.id)
    db.add(link)
    db.commit()
    print("Parent linked to student.")

print(f"\nCREDENTIALS:")
print(f"DIRECTOR: director_{school.center_code}@demo.com / 123456")
print(f"PARENT:   {parent_email} / 123456")
