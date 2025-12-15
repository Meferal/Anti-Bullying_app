import sys
import os
import random
import secrets
from datetime import datetime, timedelta

# Add current directory to path
sys.path.append(os.getcwd())

from app.database import SessionLocal
from app.models import User, UserRole, School, Student, SurveyResponse, AlertLevel, ParentStudentLink
from app.security import get_password_hash

# Configuration
TOTAL_NEW_SURVEYS = 12000
CRITICAL_SCHOOL_PERCENTAGE = 0.20

# Date range: recent
START_DATE = datetime(2025, 11, 1)
END_DATE = datetime(2025, 12, 15)

def get_random_date(start, end):
    delta = end - start
    random_days = random.randrange(delta.days)
    return start + timedelta(days=random_days)

def seed_parents():
    db = SessionLocal()
    print("👨‍👩‍👧‍👦 Seeding Parent Surveys...")
    
    # 0. Clean old surveys (User Request)
    print("🧹 Cleaning old survey responses...")
    db.query(SurveyResponse).delete()
    db.commit()
    
    # 1. Identify Active Schools (those with students)
    # We query schools that have at least one student
    active_schools = db.query(School).join(Student).distinct().all()
    
    if not active_schools:
        print("❌ No active schools found. Run seed_large_db.py first.")
        return

    num_active = len(active_schools)
    print(f"✅ Found {num_active} active schools.")
    
    # 2. Select Critical Targets (20%)
    num_critical = int(num_active * CRITICAL_SCHOOL_PERCENTAGE)
    critical_schools = random.sample(active_schools, num_critical)
    critical_ids = {s.id for s in critical_schools}
    
    print(f"🎯 Targeted {num_critical} schools for CRITICAL status.")
    
    # 3. Distribute 12,000 surveys
    # We will iterate through schools and students.
    # To get exactly 12,000, we might need multiple passes or partial passes.
    # Simple approach: 1 survey per student for established students until we hit 12k.
    # If we have 12k students exactly (which we do from previous seed), 1 per student is perfect.
    
    # Pre-compute hash for speed (approx 100x faster)
    common_password_hash = get_password_hash("123456")
    
    surveys_created = 0
    parents_created = 0
    
    # Bulk buffer
    batch_surveys = []
    
    for school in active_schools:
        # Determine risk profile for this batch
        is_critical_target = school.id in critical_ids
        
        students = db.query(Student).filter(Student.school_id == school.id).all()
        
        for student in students:
            if surveys_created >= TOTAL_NEW_SURVEYS:
                break
                
            # 4. Ensure Parent Exists
            # Check if student has parent
            # Ideally we check ParentStudentLink but for speed we might just create one 
            # or check if we already made one for this student in this run.
            # Let's verify DB for existing parent to avoid duplicates if re-run, 
            # but assume clean slate for parents mostly.
            
            # Use deterministic email for parent based on student to check existence
            parent_email = f"parent_{student.internal_code}@demo.com".lower()
            
            parent = db.query(User).filter(User.email == parent_email).first()
            if not parent:
                parent = User(
                    email=parent_email,
                    full_name=f"Padre de {student.internal_code}",
                    hashed_password=common_password_hash,
                    role=UserRole.PARENT,
                    school_id=None
                )
                db.add(parent)
                db.flush() # Need ID
                
                # Link
                link = ParentStudentLink(parent_id=parent.id, student_id=student.id)
                db.add(link)
                parents_created += 1
            
            # 5. Generate Survey Response with Real Structure
            # Risk Simulation
            import json
            
            # Logic for Risk
            survey_data = {}
            if is_critical_target:
                # 80% chance of High/Critical
                # Simulate high values for items 1-13 (0-4 scale)
                # Critical means mostly 3s and 4s
                if random.random() < 0.8:
                    score = random.randint(75, 100)
                    level = AlertLevel.CRITICAL if score > 85 else AlertLevel.HIGH
                    # Generate specific high answers
                    for i in range(1, 14):
                        survey_data[f"p_item_{i}"] = random.choice([3, 4])
                    survey_data["p_observations"] = "El alumno muestra signos claros de ansiedad y miedo."
                else:
                    score = random.randint(0, 60)
                    level = AlertLevel.LOW if score < 40 else AlertLevel.MEDIUM
                    for i in range(1, 14):
                        survey_data[f"p_item_{i}"] = random.choice([1, 2])
                    survey_data["p_observations"] = "Comportamiento normal con algunas preocupaciones."
            else:
                # Normal distribution (mostly healthy)
                if random.random() < 0.9:
                    score = random.randint(0, 40)
                    level = AlertLevel.LOW
                    for i in range(1, 14):
                        survey_data[f"p_item_{i}"] = random.choice([0, 1])
                    survey_data["p_observations"] = "Sin incidencias."
                else:
                    score = random.randint(41, 70)
                    level = AlertLevel.MEDIUM
                    for i in range(1, 14):
                        survey_data[f"p_item_{i}"] = random.choice([1, 2, 3])
                    survey_data["p_observations"] = "Leves conflictos con compañeros."

            survey = SurveyResponse(
                submitted_by_id=parent.id,
                student_id=student.id,
                date_submitted=get_random_date(START_DATE, END_DATE),
                raw_answers=json.dumps(survey_data),
                calculated_risk_score=score,
                risk_level=level,
                ai_summary="Análisis automático basado en respuestas simuladas."
            )
            batch_surveys.append(survey)
            surveys_created += 1
            
            if len(batch_surveys) >= 1000:
                db.bulk_save_objects(batch_surveys)
                db.commit()
                batch_surveys = []
                print(f"   Saved {surveys_created} surveys...")
        
        if surveys_created >= TOTAL_NEW_SURVEYS:
            break
            
    if batch_surveys:
        db.bulk_save_objects(batch_surveys)
        db.commit()
        
    print(f"🚀 Done! Created {parents_created} parents and {surveys_created} surveys.")
    db.close()

if __name__ == "__main__":
    seed_parents()
