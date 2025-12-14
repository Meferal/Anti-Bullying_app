import sqlite3

def add_column_if_not_exists(cursor, table, column, definition):
    cursor.execute(f"PRAGMA table_info({table})")
    columns = [info[1] for info in cursor.fetchall()]
    if column not in columns:
        print(f"Adding column '{column}' to '{table}'...")
        cursor.execute(f"ALTER TABLE {table} ADD COLUMN {column} {definition}")
        print("Done.")
    else:
        print(f"Column '{column}' already exists in '{table}'.")

def fix_schema():
    conn = sqlite3.connect('bullying_app.db')
    cursor = conn.cursor()
    
    # Add recovery_token
    add_column_if_not_exists(cursor, "users", "recovery_token", "VARCHAR")
    
    # Just in case, check teacher_code too
    add_column_if_not_exists(cursor, "users", "teacher_code", "VARCHAR(9)")

    conn.commit()
    conn.close()
    print("Schema update complete.")

if __name__ == "__main__":
    fix_schema()
