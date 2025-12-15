from app.database import SessionLocal
from app.models import School, Student
from sqlalchemy.orm import joinedload

def check():
    db = SessionLocal()
    
    # 1. Find a school that SHOULD have students (from seeding logs we saw SCHOOL ID 24 e.g. had students, but IDs might have accumulated)
    # Let's find any school with students explicitly
    school = db.query(School).join(Student).first()
    
    if not school:
        print("❌ No school with students found in DB query!")
        return

    print(f"✅ Found active school: {school.name} (ID: {school.id})")
    
    # 2. Check relationship count
    count_query = db.query(Student).filter(Student.school_id == school.id).count()
    print(f"   Query count: {count_query}")
    
    print(f"   Relationship len: {len(school.students)}")
    
    # 3. Check specific code
    print(f"   Center Code: {school.center_code}")
    
    # 4. Check if we can eager load
    school_eager = db.query(School).options(joinedload(School.students)).filter(School.id == school.id).first()
    print(f"   Eager load len: {len(school_eager.students)}")

    db.close()

if __name__ == "__main__":
    check()
