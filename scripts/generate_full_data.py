
import random
from datetime import datetime, timedelta
import sys
import os
import uuid

# Add parent dir to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import SessionLocal, engine, Base
from app.models import School, User, UserRole, Student, SurveyResponse, AlertLevel, ClassObservation
from app.security import get_password_hash
from app.schemas import SurveyInput, YesNo, Frequency

# Ensure tables exist
Base.metadata.create_all(bind=engine)

def get_coordinates_for_zip(zip_code):
    # Approximation around Valencia
    # 39.4699, -0.3763
    # Offset slightly based on zip (fake logic)
    offset = int(zip_code) - 46000
    lat = 39.4699 + (offset * 0.001 * (1 if offset % 2 == 0 else -1))
    lon = -0.3763 + (offset * 0.001 * (1 if offset % 3 == 0 else -1))
    return lat, lon

def generate_weekly_dates(start_date, end_date):
    current = start_date
    while current <= end_date:
        yield current
        current += timedelta(weeks=1)

def create_survey_response(db, student_id, submitter_id, risk_profile):
    """
    risk_profile: 'green', 'orange', 'red'
    """
    # Create SurveyInput (Generic data to match score)
    # We will just write directly to DB to save time, or use heuristic logic?
    # Better to write DB object directly to ensure Score matches Risk Level explicitly.
    
    score = 0
    risk = AlertLevel.LOW
    flags = []
    
    if risk_profile == 'green':
        score = random.randint(0, 5)
        risk = AlertLevel.LOW
        
    elif risk_profile == 'orange':
        score = random.randint(10, 18)
        risk = AlertLevel.HIGH # Orange map usually means High or Medium? 
        # In current logic: Medium > 8, High > 15.
        if score > 15: risk = AlertLevel.HIGH
        else: risk = AlertLevel.MEDIUM
        flags = ["Indicadores leves"]

    elif risk_profile == 'red':
        score = random.randint(26, 40)
        risk = AlertLevel.CRITICAL
        flags = ["Marcadores críticos", "Violencia física"]

    # We mock the raw JSON to be valid but empty
    
    survey = SurveyResponse(
        date_submitted=datetime.now(),
        submitted_by_id=submitter_id,
        student_id=student_id,
        raw_answers='{"generated": true}',
        calculated_risk_score=score,
        risk_level=risk,
        ai_summary=f"Simulated report for {risk_profile} profile."
    )
    db.add(survey)
    return survey

def main():
    db = SessionLocal()
    print("Starting massive seed generation...")

    start_date = datetime(2025, 9, 1)
    end_date = datetime.now()

    try:
        # Loop Zip Codes 46001 - 46025
        for zip_num in range(46001, 46026):
            zip_str = str(zip_num)
            print(f"Processing Zip {zip_str}...")

            # 3 Schools: Green, Orange, Red
            risk_types = ['green', 'orange', 'red']
            
            for i, risk_type in enumerate(risk_types):
                lat, lon = get_coordinates_for_zip(zip_num)
                # Scatter them slightly
                lat += random.uniform(-0.005, 0.005)
                lon += random.uniform(-0.005, 0.005)
                
                center_code = f"VAL-{zip_str}-{risk_type.upper()}-{i}"
                school_name = f"Colegio Valencia {zip_str} {risk_type.title()}"
                
                # Create School
                school = School(
                    center_code=center_code,
                    name=school_name,
                    address=f"Calle Falsa {i}, {zip_str}, Valencia",
                    latitude=lat,
                    longitude=lon,
                    contact_email=f"contact@{center_code}.com",
                    is_active=True
                )
                db.add(school)
                db.commit() # Commit to get ID
                db.refresh(school)

                # Create Teacher
                # Teacher code must be unique and max 9 chars. 
                # Use T- plus 7 random hex chars
                import uuid
                teacher_code = f"T-{uuid.uuid4().hex[:7].upper()}"
                teacher = User(
                    email=f"prof_{center_code}@demo.com".lower(),
                    hashed_password=get_password_hash("123456"),
                    full_name=f"Profesor {risk_type.title()} {zip_str}",
                    role=UserRole.TEACHER,
                    school_id=school.id,
                    teacher_code=teacher_code
                )
                db.add(teacher)
                db.commit()
                db.refresh(teacher)

                # Create Students (Class 5A)
                num_students = 15
                students = []
                for s_idx in range(num_students):
                    student = Student(
                        internal_code=f"S-{center_code}-{s_idx}",
                        age=10,
                        grade_class="5A",
                        school_id=school.id,
                        teacher_id=teacher.id
                    )
                    db.add(student)
                    students.append(student)
                db.commit()
                for s in students: db.refresh(s)

                # Generate Weekly Class Reports
                for date in generate_weekly_dates(start_date, end_date):
                    obs_content = f"Semana {date.strftime('%Y-%m-%d')}: Todo normal."
                    if risk_type == 'orange' and random.random() > 0.7:
                        obs_content = f"Semana {date.strftime('%Y-%m-%d')}: Pequeños conflictos en el patio."
                    elif risk_type == 'red' and random.random() > 0.5:
                        obs_content = f"Semana {date.strftime('%Y-%m-%d')}: Conflictos graves observados entre alumnos."

                    obs = ClassObservation(
                        teacher_id=teacher.id,
                        content=obs_content,
                        timestamp=date
                    )
                    db.add(obs)

                # Generate Student Surveys (To drive Map Colors)
                # Green School: 100% Green
                # Orange School: 20% Orange
                # Red School: 20% Red
                
                for student in students:
                    # Decide student risk profile
                    s_risk = 'green'
                    if risk_type == 'orange' and random.random() < 0.3:
                        s_risk = 'orange'
                    elif risk_type == 'red' and random.random() < 0.3:
                        s_risk = 'red'
                    
                    # Create 1 report per student (recent)
                    create_survey_response(db, student.id, teacher.id, s_risk)
                
                db.commit()

        print("Finished generating seed data.")

    except Exception as e:
        print(f"Error: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    main()
