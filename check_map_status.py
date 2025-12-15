from app.database import SessionLocal
from app.models import School, Student, SurveyResponse, AlertLevel
from collections import defaultdict
from sqlalchemy import or_

def check_status():
    db = SessionLocal()
    
    # 1. Fetch schools like the API does
    schools = db.query(School).filter(
        School.latitude.isnot(None),
        School.longitude.isnot(None)
    ).all()
    
    print(f"Total Schools on Map: {len(schools)}")
    
    # 2. Fetch Aggregated Data
    results = db.query(
        Student.school_id, 
        SurveyResponse.risk_level
    ).join(SurveyResponse).all()
    
    school_risks = defaultdict(list)
    for s_id, r_level in results:
        school_risks[s_id].append(r_level)
        
    # 3. Apply Traffic Light Logic
    status_counts = {"red": 0, "orange": 0, "green": 0}
    red_examples = []
    
    for school in schools:
        traffic_light = "green"
        if school.id in school_risks:
            risks = school_risks[school.id]
            
            if AlertLevel.CRITICAL in risks:
                traffic_light = "red"
                if len(red_examples) < 5:
                    red_examples.append(school.name)
            elif AlertLevel.HIGH in risks:
                 traffic_light = "orange"
        
        status_counts[traffic_light] += 1
        
    print(f"Status Distribution: {status_counts}")
    print("Examples of RED schools:")
    for name in red_examples:
        print(f" - {name}")

    db.close()

if __name__ == "__main__":
    check_status()
