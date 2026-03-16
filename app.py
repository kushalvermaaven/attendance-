from flask import Flask, render_template, request, redirect, session
import sqlite3
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = "attendance_secret"

DATABASE = "database.db"


# -----------------------------
# DATABASE CONNECTION
# -----------------------------

def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


# -----------------------------
# AUTO DATABASE INITIALIZATION
# -----------------------------

def init_db():

    conn = get_db()
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
    check_out_time TEXT,
    status TEXT
    )
    """)

    # DEFAULT ADMIN
    admin = cursor.execute(
        "SELECT * FROM users WHERE email='admin@company.com'"
    ).fetchone()

    if not admin:

        password = generate_password_hash("admin123")

        cursor.execute("""
        INSERT INTO users
        (name,email,password,role,department,technical_role,created_at)
        VALUES (?,?,?,?,?,?,?)
        """,(
        "Admin",
        "admin@company.com",
        password,
        "admin",
        "Management",
        "Administrator",
        datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        ))


    # TANPRISH ADMIN
    tanprish = cursor.execute(
        "SELECT * FROM users WHERE email='tanprishdynamics@gmail.com'"
    ).fetchone()

    if not tanprish:

        password = generate_password_hash("Tanprish@123")

        cursor.execute("""
        INSERT INTO users
        (name,email,password,role,department,technical_role,created_at)
        VALUES (?,?,?,?,?,?,?)
        """,(
        "Tanprish Admin",
        "tanprishdynamics@gmail.com",
        password,
        "admin",
        "Management",
        "Administrator",
        datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        ))

    conn.commit()
    conn.close()


# run once when server starts
init_db()

# -----------------------------
# LOGIN
# -----------------------------

@app.route("/", methods=["GET","POST"])
def login():

    if request.method == "POST":

        email = request.form["email"]
        password = request.form["password"]

        conn = get_db()

        user = conn.execute(
            "SELECT * FROM users WHERE email=?",
            (email,)
        ).fetchone()

        if user and check_password_hash(user["password"],password):

            session["user_id"] = user["id"]
            session["role"] = user["role"]
            session["name"] = user["name"]

            return redirect("/"+user["role"])

        return "Invalid login"

    return render_template("login.html")


# -----------------------------
# LOGOUT
# -----------------------------

@app.route("/logout")
def logout():

    session.clear()
    return redirect("/")


# -----------------------------
# ADMIN DASHBOARD
# -----------------------------

@app.route("/admin")
def admin_dashboard():

    if session.get("role") != "admin":
        return redirect("/")

    conn = get_db()

    emp = conn.execute(
        "SELECT COUNT(*) FROM users WHERE role='employee'"
    ).fetchone()[0]

    intern = conn.execute(
        "SELECT COUNT(*) FROM users WHERE role='intern'"
    ).fetchone()[0]

    hr = conn.execute(
        "SELECT COUNT(*) FROM users WHERE role='hr'"
    ).fetchone()[0]

    return render_template(
        "admin_dashboard.html",
        emp=emp,
        intern=intern,
        hr=hr
    )


# -----------------------------
# HR DASHBOARD
# -----------------------------

@app.route("/hr")
def hr_dashboard():

    if session.get("role") != "hr":
        return redirect("/")

    return render_template("hr_dashboard.html")


# -----------------------------
# EMPLOYEE DASHBOARD
# -----------------------------

@app.route("/employee")
def employee_dashboard():

    if session.get("role") != "employee":
        return redirect("/")

    return render_template("employee_dashboard.html")


# -----------------------------
# INTERN DASHBOARD
# -----------------------------

@app.route("/intern")
def intern_dashboard():

    if session.get("role") != "intern":
        return redirect("/")

    return render_template("intern_dashboard.html")


# -----------------------------
# ADD USER
# -----------------------------

@app.route("/add_user", methods=["GET","POST"])
def add_user():

    if session.get("role") not in ["admin","hr"]:
        return redirect("/")

    if request.method == "POST":

        name = request.form["name"]
        email = request.form["email"]
        password = generate_password_hash(request.form["password"])
        role = request.form["role"]
        department = request.form["department"]
        tech = request.form["technical_role"]

        conn = get_db()

        conn.execute("""
        INSERT INTO users
        (name,email,password,role,department,technical_role,created_at)
        VALUES (?,?,?,?,?,?,?)
        """,(
        name,email,password,role,department,tech,
        datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        ))

        conn.commit()

        return redirect("/manage_users")

    return render_template("add_user.html")


# -----------------------------
# MANAGE USERS
# -----------------------------

@app.route("/manage_users")
def manage_users():

    if session.get("role") not in ["admin","hr"]:
        return redirect("/")

    conn = get_db()

    users = conn.execute(
        "SELECT * FROM users"
    ).fetchall()

    return render_template("manage_users.html",users=users)


# -----------------------------
# MARK ATTENDANCE
# -----------------------------

@app.route("/mark_attendance")
def mark_attendance():

    user_id = session.get("user_id")

    if not user_id:
        return redirect("/")

    conn = get_db()

    today = datetime.now().strftime("%Y-%m-%d")
    time_now = datetime.now().strftime("%H:%M:%S")

    attendance = conn.execute(
        "SELECT * FROM attendance WHERE user_id=? AND date=?",
        (user_id, today)
    ).fetchone()

    # FIRST CLICK → CHECK IN
    if attendance is None:

        conn.execute("""
        INSERT INTO attendance
        (user_id, date, check_in_time, check_out_time, status)
        VALUES (?, ?, ?, ?, ?)
        """, (
            user_id,
            today,
            time_now,
            None,
            "Present"
        ))

        conn.commit()

        return "Check-in recorded successfully"


    # SECOND CLICK → CHECK OUT
    elif attendance["check_out_time"] is None:

        conn.execute("""
        UPDATE attendance
        SET check_out_time=?
        WHERE user_id=? AND date=?
        """, (
            time_now,
            user_id,
            today
        ))

        conn.commit()

        return "Check-out recorded successfully"


    # THIRD CLICK → ALREADY COMPLETED
    else:
        return "Attendance already completed for today"

# -----------------------------
# ATTENDANCE HISTORY
# -----------------------------

@app.route("/attendance_history")
def attendance_history():

    user_id = session.get("user_id")

    conn = get_db()

    data = conn.execute(
        "SELECT * FROM attendance WHERE user_id=?",
        (user_id,)
    ).fetchall()

    return render_template(
        "attendance_history.html",
        data=data
    )


# -----------------------------
# RUN SERVER
# -----------------------------

if __name__ == "__main__":
    app.run(debug=True)

# -----------------------------
# VIEW ATTENDANCE (ADMIN / HR)
# -----------------------------

@app.route("/view_attendance")
def view_attendance():

    if session.get("role") not in ["admin", "hr"]:
        return redirect("/")

    conn = get_db()

    date = request.args.get("date")

    if date:

        employee_data = conn.execute("""
        SELECT users.name, attendance.date,
        attendance.check_in_time,
        attendance.check_out_time,
        attendance.status
        FROM attendance
        JOIN users ON users.id = attendance.user_id
        WHERE users.role='employee'
        AND attendance.date=?
        """,(date,)).fetchall()

        intern_data = conn.execute("""
        SELECT users.name, attendance.date,
        attendance.check_in_time,
        attendance.check_out_time,
        attendance.status
        FROM attendance
        JOIN users ON users.id = attendance.user_id
        WHERE users.role='intern'
        AND attendance.date=?
        """,(date,)).fetchall()

    else:

        employee_data = conn.execute("""
        SELECT users.name, attendance.date,
        attendance.check_in_time,
        attendance.check_out_time,
        attendance.status
        FROM attendance
        JOIN users ON users.id = attendance.user_id
        WHERE users.role='employee'
        """).fetchall()

        intern_data = conn.execute("""
        SELECT users.name, attendance.date,
        attendance.check_in_time,
        attendance.check_out_time,
        attendance.status
        FROM attendance
        JOIN users ON users.id = attendance.user_id
        WHERE users.role='intern'
        """).fetchall()

    return render_template(
        "view_attendance.html",
        employee_data=employee_data,
        intern_data=intern_data
    )