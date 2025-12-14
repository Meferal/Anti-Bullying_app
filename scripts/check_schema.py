import sqlite3

def check_schema():
    conn = sqlite3.connect('bullying_app.db')
    cursor = conn.cursor()
    
    # List tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = [t[0] for t in cursor.fetchall()]
    print("Tables found:", tables)
    
    if "chat_messages" in tables:
        print("\n[OK] 'chat_messages' table exists.")
        cursor.execute("PRAGMA table_info(chat_messages)")
        print(cursor.fetchall())
    else:
        print("\n[!] MISSING 'chat_messages' table!")

    conn.close()

if __name__ == "__main__":
    check_schema()
