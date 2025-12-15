from app.database import SessionLocal
from app.models import School

def check():
    db = SessionLocal()
    
    total = db.query(School).count()
    valid_coords = db.query(School).filter(School.latitude.isnot(None), School.longitude.isnot(None)).count()
    
    print(f"Total Schools: {total}")
    print(f"Schools with Coords: {valid_coords}")
    
    # Sample one
    first = db.query(School).filter(School.latitude.isnot(None)).first()
    if first:
        print(f"Sample: {first.name} ({first.latitude}, {first.longitude})")
        
    db.close()

if __name__ == "__main__":
    check()
