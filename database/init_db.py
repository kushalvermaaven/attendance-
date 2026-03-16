# ATTENDANCE TABLE
cursor.execute("""
CREATE TABLE IF NOT EXISTS attendance(
id INTEGER PRIMARY KEY AUTOINCREMENT,
user_id INTEGER,
date TEXT,
check_in_time TEXT,
check_out_time TEXT,
status TEXT
)
""")