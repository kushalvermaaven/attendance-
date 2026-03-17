import sqlite3
from werkzeug.security import generate_password_hash

conn = sqlite3.connect("database.db")
cursor = conn.cursor()

# USERS TABLE
cursor.execute("""
CREATE TABLE IF NOT EXISTS users(
id INTEGER PRIMARY KEY AUTOINCREMENT,
name TEXT,
email TEXT UNIQUE,
password TEXT,
role TEXT,
department TEXT,
technical_role TEXT,
created_at TEXT
)
""")

# ATTENDANCE TABLE
cursor.execute("""
CREATE TABLE IF NOT EXISTS attendance(
id INTEGER PRIMARY KEY AUTOINCREMENT,
user_id INTEGER,
date TEXT,
check_in_time TEXT,
status TEXT
)
""")

# CREATE DEFAULT ADMIN
password = generate_password_hash("admin123")

cursor.execute("""
INSERT INTO users(name,email,password,role,department,technical_role,created_at)
VALUES (?,?,?,?,?,?,datetime('now'))
""",(
"Admin",
"admin@company.com",
password,
"admin",
"Management",
"Administrator"
))

conn.commit()
conn.close()

print("Database Created Successfully")

leave_requests
id
user_id
start_date
end_date
reason
status

