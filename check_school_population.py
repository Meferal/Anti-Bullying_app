from app.database import SessionLocal
from app.models import School, Student
from sqlalchemy import func

def check_population():
    db = SessionLocal()
    
    total_schools = db.query(School).count()
    
    # Schools with at least one student
    active_schools_count = db.query(School.id).join(Student).distinct().count()
    
    empty_schools_count = total_schools - active_schools_count
    
    print(f"Total Schools: {total_schools}")
    print(f"Schools WITH Students: {active_schools_count}")
    print(f"Schools WITHOUT Students: {empty_schools_count}")
    
    if active_schools_count > 0:
        print(f"Coverage: {(active_schools_count/total_schools)*100:.1f}%")
    
    # List first 5 empty schools as examples
    if empty_schools_count > 0:
        print("\nExamples of Empty Schools:")
        empty_schools = db.query(School).outerjoin(Student).filter(Student.id == None).limit(5).all()
        for s in empty_schools:
            print(f" - {s.name} ({s.center_code})")
            
    db.close()

if __name__ == "__main__":
    check_population()
