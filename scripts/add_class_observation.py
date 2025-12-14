import sqlite3

def add_class_observation_table():
    conn = sqlite3.connect('bullying_app.db')
    cursor = conn.cursor()
    
    print("Checking for 'class_observations' table...")
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='class_observations';")
    if cursor.fetchone():
        print("Table 'class_observations' already exists.")
    else:
        print("Creating 'class_observations' table...")
        # Simple schema: id, teacher_id, content, date
        cursor.execute("""
            CREATE TABLE class_observations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                teacher_id INTEGER,
                content TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(teacher_id) REFERENCES users(id)
            )
        """)
        print("Done.")

    conn.commit()
    conn.close()

if __name__ == "__main__":
    add_class_observation_table()
