import sys
import os
import random
from datetime import datetime, timedelta
import secrets

# Add current directory to path so we can import app modules
sys.path.append(os.getcwd())

from sqlalchemy.orm import Session
from app.database import engine, SessionLocal, Base
from app.models import (
    User, UserRole, School, Student, SurveyResponse, AlertLevel, ParentStudentLink
)
from app.security import get_password_hash

# --- Configuration ---
NUM_SCHOOLS = 40
CLASSES_PER_GRADE = 3
GRADES = 4 # 1, 2, 3, 4
STUDENTS_PER_CLASS = 25
TOTAL_STUDENTS = NUM_SCHOOLS * GRADES * CLASSES_PER_GRADE * STUDENTS_PER_CLASS

# Date range for surveys: Sept 1 to Nov 30 (approx 13 weeks)
START_DATE = datetime(2025, 9, 1)
END_DATE = datetime(2025, 11, 30)

def get_weeks(start_date, end_date):
    weeks = []
    curr = start_date
    while curr < end_date:
        weeks.append(curr)
        curr += timedelta(days=7)
    return weeks

WEEKS = get_weeks(START_DATE, END_DATE)

def reset_db():
    print("🗑️  Dropping all tables...")
    Base.metadata.drop_all(bind=engine)
    print("✨  Creating all tables...")
    Base.metadata.create_all(bind=engine)

def create_super_admin(db: Session):
    print("🦸 Creating Super Admin: Maria...")
    sa = User(
        email="maria@conselleria.es",
        full_name="Maria",
        hashed_password=get_password_hash("Maria12345@"),
        role=UserRole.SUPER_ADMIN,
        school_id=None
    )
    db.add(sa)
    return sa

def generate_risk_profile():
    # 30% Red, 30% Orange, 40% Green
    r = random.random()
    if r < 0.3: return "RED"
    elif r < 0.6: return "ORANGE"
    else: return "GREEN"

def get_survey_data(risk_profile):
    """
    Returns (score, level, answers, summary) based on profile
    """
    if risk_profile == "RED":
        # Bias towards High/Critical
        score = random.randint(60, 100)
        level = AlertLevel.HIGH if score < 85 else AlertLevel.CRITICAL
    elif risk_profile == "ORANGE":
        # Bias towards Medium
        score = random.randint(30, 70)
        level = AlertLevel.MEDIUM if score > 50 else AlertLevel.LOW
    else:
        # Bias towards Low
        score = random.randint(0, 40)
        level = AlertLevel.LOW if score < 30 else AlertLevel.MEDIUM
    
    return score, level

import pandas as pd
import math

def seed():
    db = SessionLocal()
    reset_db()
    
    create_super_admin(db)
    
    print("📂 Reading documents/valencia.xls...")
    try:
        df = pd.read_excel("documents/valencia.xls")
        # Ensure column mapping
        # Codigo, Denominacion, Tipo_Via, Direccion, Num, Codigo_postal, Localidad, Provincia, Telefono, long, lat
    except Exception as e:
        print(f"❌ Error reading Excel: {e}")
        return

    # Select 40 schools indices to be 'active' (have students)
    total_schools_in_file = len(df)
    active_indices = set(random.sample(range(total_schools_in_file), min(NUM_SCHOOLS, total_schools_in_file)))
    
    print(f"🏫 Processing {total_schools_in_file} schools from file...")
    print(f"   (Populating {len(active_indices)} of them with {TOTAL_STUDENTS} students total)")

    for index, row in df.iterrows():
        # Parsing data
        center_code = str(row['Codigo']).split('.')[0] # Handle float conversion if any
        raw_name = row['Denominacion']
        locality = str(row['Localidad']) if pd.notna(row['Localidad']) else ""
        
        # Unique name for UX
        name = f"{raw_name} ({locality})"
        
        # Address reconstruction
        via_type = str(row['Tipo_Via']) if pd.notna(row['Tipo_Via']) else ""
        address_name = str(row['Direccion']) if pd.notna(row['Direccion']) else ""
        num = str(row['Num']) if pd.notna(row['Num']) else ""
        postal_code = str(row['Codigo_postal']).split('.')[0] if pd.notna(row['Codigo_postal']) else ""
        locality = str(row['Localidad']) if pd.notna(row['Localidad']) else ""
        
        full_address = f"{via_type} {address_name} {num}, {postal_code} {locality}".strip()
        
        latitude = row['lat']
        longitude = row['long']
        phone = str(row['Telefono']).split('.')[0] if pd.notna(row['Telefono']) else None
        
        # Determine profile (random)
        school_profile = generate_risk_profile()
        
        # Create School
        school = School(
            name=name,
            center_code=center_code,
            address=full_address,
            latitude=latitude,
            longitude=longitude,
            contact_email=f"director_{center_code}@demo.com",
            phone=phone
        )
        db.add(school)
        db.flush()
        
        # Create Director
        director = User(
            email=f"director_{center_code}@demo.com",
            full_name=f"Director {name}",
            hashed_password=get_password_hash("123456"),
            role=UserRole.SCHOOL_ADMIN,
            school_id=school.id,
            teacher_code=f"DIR-{center_code}"
        )
        db.add(director)
        
        # Only populate classes/students if in active set
        if index in active_indices:
            grade_letters = ["A", "B", "C"]
            for g in range(1, GRADES + 1):
                for letter in grade_letters:
                    cls_name = f"{g}º {letter}"
                    t_email = f"prof_{center_code}_{g}{letter}@demo.com".lower()
                    
                    teacher = User(
                        email=t_email,
                        full_name=f"Prof. {cls_name} - {name[:20]}...",
                        hashed_password=get_password_hash("123456"),
                        role=UserRole.TEACHER,
                        school_id=school.id,
                        teacher_code=f"T-{center_code}-{g}{letter}" # Full length
                    )
                    
                    # Check duplicate email (unlikely but safe)
                    if db.query(User).filter(User.email == t_email).first():
                        t_email = f"prof_{center_code}_{g}{letter}_{secrets.token_hex(2)}@demo.com".lower()
                        teacher.email = t_email

                    db.add(teacher)
                    db.flush()
                    
                    batch_surveys = []
                    for s_idx in range(1, STUDENTS_PER_CLASS + 1):
                        s_code = secrets.token_hex(4).upper()
                        student = Student(
                            internal_code=s_code,
                            age=6 + g,
                            grade_class=cls_name,
                            school_id=school.id,
                            teacher_id=teacher.id
                        )
                        db.add(student)
                        db.flush()
                        
                        # Surveys
                        for w_date in WEEKS:
                            score, level = get_survey_data(school_profile)
                            if random.random() < 0.2:
                                 score, level = get_survey_data("GREEN" if school_profile == "RED" else "RED")

                            surv = SurveyResponse(
                                submitted_by_id=student.id,
                                student_id=student.id,
                                date_submitted=w_date + timedelta(days=random.randint(0,4)),
                                raw_answers="{}",
                                calculated_risk_score=score,
                                risk_level=level,
                                ai_summary="Generated mock summary."
                            )
                            batch_surveys.append(surv)
                    
                    db.bulk_save_objects(batch_surveys)
        
        if index % 50 == 0:
            print(f"   Processed {index} schools...")
            db.commit() # Periodic commit

    print("🚀 Seeding complete!")
    db.commit()
    db.close()


if __name__ == "__main__":
    seed()
