import sqlite3

print("Dropping invitation-related tables...")

conn = sqlite3.connect("../../example.db")
conn.execute("PRAGMA foreign_keys = OFF")

# Drop invitation-related tables
conn.execute("DROP TABLE IF EXISTS invitations")
conn.execute("DROP TABLE IF EXISTS invitation_links")

# Create temporary tables without invitation-related columns
conn.execute("""
    CREATE TABLE users_temp AS 
    SELECT uuid, chat_id, role, name, teacher_subjects, parent_children, created_at, updated_at 
    FROM users
""")

conn.execute("""
    CREATE TABLE classes_temp AS 
    SELECT uuid, start_year, class_name, created_at, updated_at, school_uuid, homeroom_teacher_uuid 
    FROM classes
""")

conn.execute("""
    CREATE TABLE subjects_temp AS 
    SELECT uuid, name, created_at, updated_at, class_uuid 
    FROM subjects
""")

# Drop original tables
conn.execute("DROP TABLE users")
conn.execute("DROP TABLE classes")
conn.execute("DROP TABLE subjects")

# Rename temporary tables
conn.execute("ALTER TABLE users_temp RENAME TO users")
conn.execute("ALTER TABLE classes_temp RENAME TO classes")
conn.execute("ALTER TABLE subjects_temp RENAME TO subjects")

conn.commit()
conn.close()

print("Done!") 