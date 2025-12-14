
import pandas as pd
import sys
import os
import random
from datetime import datetime, timedelta
import uuid

# Add parent dir to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import SessionLocal, engine, Base
from app.models import School, User, UserRole, Student, SurveyResponse, AlertLevel
from app.security import get_password_hash

# Ensure tables exist
Base.metadata.create_all(bind=engine)

def generate_weekly_dates(start_date, end_date):
    current = start_date
    while current <= end_date:
        yield current
        current += timedelta(weeks=1)

def create_survey(db, student_id, parent_id, risk_type, date):
    # Check if a report exists for this student within 3 days of this date
    start_window = date - timedelta(days=3)
    end_window = date + timedelta(days=3)
    existing = db.query(SurveyResponse).filter(
        SurveyResponse.student_id == student_id,
        SurveyResponse.date_submitted >= start_window,
        SurveyResponse.date_submitted <= end_window
    ).first()
    
    if existing:
        return

    # Simulate Parent Input (0-4 items)
    # p_item_1..13
    
    # Defaults
    items = {f"p_item_{i}": 0 for i in range(1, 14)}
    
    if risk_type == 'green':
        # Mostly 0s, occasional 1
        for k in items:
            if random.random() < 0.1: items[k] = 1
            
    elif risk_type == 'orange':
        # Moderate scores (some 1s and 2s)
        # Focus on items 6-10 (Psychosomatic)
        for i in range(6, 11):
            items[f"p_item_{i}"] = random.choice([1, 2, 3])
        # Some 1s in others
        for k in items:
             if items[k] == 0 and random.random() < 0.2: items[k] = 1

    elif risk_type == 'red':
        # High scores (3s and 4s)
        # Direct indicators (1-5)
        for i in range(1, 6):
            if random.random() < 0.7: items[f"p_item_{i}"] = random.choice([3, 4])
        # Cyber (11-13)
        if random.random() < 0.5:
             for i in range(11, 14): items[f"p_item_{i}"] = random.choice([2, 3, 4])

    # Calculate Score for DB (Use simple sum logic match)
    score_a = sum([items[f"p_item_{i}"] for i in range(1, 6)])
    score_b = sum([items[f"p_item_{i}"] for i in range(6, 11)])
    score_c = sum([items[f"p_item_{i}"] for i in range(11, 14)])
    total_score = score_a + score_b + score_c
    
    # Determine Risk Level
    risk_level = AlertLevel.LOW
    if total_score > 25: risk_level = AlertLevel.CRITICAL
    elif total_score > 15: risk_level = AlertLevel.HIGH
    elif total_score > 8: risk_level = AlertLevel.MEDIUM

    # Raw Json Mock
    import json
    raw_json = json.dumps(items)
    
    survey = SurveyResponse(
        date_submitted=date,
        submitted_by_id=parent_id,
        student_id=student_id,
        raw_answers=raw_json,
        calculated_risk_score=total_score,
        risk_level=risk_level,
        ai_summary=f"Report generated from Excel import. Profile: {risk_type}"
    )
    db.add(survey)


def main():
    file_path = "c:/Users/Alvaro/Documents/GitHub/Anti-Bullyng_app/documents/valencia.xls"
    print(f"Reading {file_path}...")
    
    try:
        df = pd.read_excel(file_path)
    except Exception as e:
        print(f"Error reading Excel: {e}")
        return

    # Filter Zip Codes 46001 - 46025
    # Ensure Codigo_postal is string
    df['Codigo_postal'] = df['Codigo_postal'].apply(lambda x: str(int(x)) if pd.notnull(x) else '')
    
    target_zips = [str(z) for z in range(46001, 46026)]
    
    df_filtered = df[df['Codigo_postal'].isin(target_zips)]
    print(f"Found {len(df_filtered)} schools in target zip codes.")

    db = SessionLocal()
    start_date = datetime(2025, 9, 1)
    end_date = datetime.now()

    try:
        grouped = df_filtered.groupby('Codigo_postal')
        
        for name, group in grouped:
            print(f"Processing Zip {name} - Found {len(group)} schools.")
            
            # Select up to 3 schools
            schools_to_process = group.head(3)
            
            risk_profiles = ['green', 'orange', 'red']
            
            for index, (idx, row) in enumerate(schools_to_process.iterrows()):
                risk_type = risk_profiles[index % 3] # Cycle if more than 3 (though we limited to 3)
                
                # School Info
                center_code = str(row['Codigo']).strip()
                raw_name = str(row['Denominacion']).strip()
                school_name = f"{raw_name} ({center_code})"
                
                # Create/Get School
                school = db.query(School).filter(School.center_code == center_code).first()
                if not school:
                    # Construct Address
                    tipo_via = str(row.get('Tipo_Via', '')).replace('nan', '')
                    direccion = str(row.get('Direccion', '')).replace('nan', '')
                    num = str(row.get('Num', '')).replace('nan', '')
                    cp = str(row.get('Codigo_postal', '')).replace('nan', '')
                    localidad = str(row.get('Localidad', '')).replace('nan', '')
                    provincia = str(row.get('Provincia', '')).replace('nan', '')
                    full_address = f"{tipo_via} {direccion} {num}, {cp} {localidad}, {provincia}".strip()

                    try:
                        lng = float(str(row['long']).replace(',', '.'))
                        lat = float(str(row['lat']).replace(',', '.'))
                    except:
                        lng, lat = None, None

                    school = School(
                        center_code=center_code,
                        name=school_name,
                        address=full_address,
                        latitude=lat,
                        longitude=lng,
                        contact_email="",
                        is_active=True
                    )
                    db.add(school)
                    db.commit()
                    db.refresh(school)
                
                print(f"  > School: {school_name} [{risk_type.upper()}]")

                # Ensure Students Exist (Create generic if needed)
                # Create 1 class of 10 students
                students = db.query(Student).filter(Student.school_id == school.id).all()
                if not students:
                    # Create Parent User for submissions
                    parent = User(
                         email=f"parent_{center_code}@demo.com",
                         hashed_password=get_password_hash("123456"),
                         full_name=f"Parent Rep {center_code}",
                         role=UserRole.PARENT,
                         school_id=school.id
                    )
                    db.add(parent)
                    db.commit()
                    db.refresh(parent)
                    
                    for i in range(10):
                         student = Student(
                             internal_code=f"S-{center_code}-{i}",
                             age=12,
                             grade_class="1ESO",
                             school_id=school.id
                         )
                         db.add(student)
                         # Link parent? Using parent_student_link table or not required for survey submission if manual?
                         # The survey submission requires submitted_by_id. 
                         # We'll use the generic parent user created above.
                         students.append(student)
                    db.commit()
                    for s in students: db.refresh(s)
                else:
                    # Reuse existing parent if possible or grab first admin
                    parent = db.query(User).filter(User.school_id == school.id, User.role == UserRole.PARENT).first()
                    if not parent:
                         parent = User(
                             email=f"parent_{center_code}@demo.com",
                             hashed_password=get_password_hash("123456"),
                             full_name=f"Parent Rep {center_code}",
                             role=UserRole.PARENT,
                             school_id=school.id
                        )
                         db.add(parent)
                         db.commit()
                         db.refresh(parent)

                # Generate Reports
                # Green School: All students Green
                # Orange: 3 students Orange, rest Green
                # Red: 3 students Red, 3 Orange, rest Green
                
                for s_idx, student in enumerate(students):
                    student_risk = 'green'
                    if risk_type == 'orange':
                        if s_idx < 3: student_risk = 'orange'
                    elif risk_type == 'red':
                        if s_idx < 3: student_risk = 'red'
                        elif s_idx < 6: student_risk = 'orange'
                    
                    # Generate Weekly reports
                    for date in generate_weekly_dates(start_date, end_date):
                        # Add some randomness to date (submission time)
                        submit_date = date + timedelta(hours=random.randint(8, 20))
                        create_survey(db, student.id, parent.id, student_risk, submit_date)
                
                db.commit()

        print("Done generate reports from Excel.")

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    main()
