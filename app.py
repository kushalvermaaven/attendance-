from flask import Flask, render_template, request, redirect, session, jsonify
import sqlite3
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import timedelta

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
# DATABASE INITIALIZATION
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

    # LEAVE REQUEST TABLE
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS leave_requests(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        start_date TEXT,
        end_date TEXT,
        reason TEXT,
        status TEXT,
        created_at TEXT
    )
    """)

    # HOLIDAYS TABLE
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS holidays(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        date TEXT
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

    # SECOND ADMIN
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


# Run database setup
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

        if user and check_password_hash(user["password"], password):

            session["user_id"] = user["id"]
            session["role"] = user["role"]
            session["name"] = user["name"]

            return redirect("/" + user["role"])

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
# DASHBOARDS
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


@app.route("/employee")
def employee_dashboard():

    if session.get("role") != "employee":
        return redirect("/")

    return render_template("employee_dashboard.html")


@app.route("/intern")
def intern_dashboard():

    if session.get("role") != "intern":
        return redirect("/")

    return render_template("intern_dashboard.html")


@app.route("/hr")
def hr_dashboard():

    if session.get("role") != "hr":
        return redirect("/")

    return render_template("hr_dashboard.html")


# -----------------------------
# PROFILE
# -----------------------------

@app.route("/profile")
def profile():

    user_id = session.get("user_id")

    if not user_id:
        return redirect("/")

    conn = get_db()

    user = conn.execute(
        "SELECT * FROM users WHERE id=?",
        (user_id,)
    ).fetchone()

    return render_template("profile.html", user=user)


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
# DELETE USER
# -----------------------------

@app.route("/delete_user/<int:user_id>")
def delete_user(user_id):

    # Only admin or HR can delete
    if session.get("role") not in ["admin","hr"]:
        return redirect("/")

    conn = get_db()

    # delete attendance records first
    conn.execute(
        "DELETE FROM attendance WHERE user_id=?",
        (user_id,)
    )

    # delete leave requests
    conn.execute(
        "DELETE FROM leave_requests WHERE user_id=?",
        (user_id,)
    )

    # delete user
    conn.execute(
        "DELETE FROM users WHERE id=?",
        (user_id,)
    )

    conn.commit()

    return redirect("/manage_users")

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

    office_time = "09:30:00"

    status = "Present"

    if time_now > office_time:
        status = "Late"

    attendance = conn.execute(
        "SELECT * FROM attendance WHERE user_id=? AND date=?",
        (user_id,today)
    ).fetchone()

    if attendance is None:

        conn.execute("""
        INSERT INTO attendance
        (user_id,date,check_in_time,check_out_time,status)
        VALUES (?,?,?,?,?)
        """,(
            user_id,
            today,
            time_now,
            None,
            status
        ))

        conn.commit()

        return "Check-in recorded"

    elif attendance["check_out_time"] is None:

        conn.execute("""
        UPDATE attendance
        SET check_out_time=?
        WHERE user_id=? AND date=?
        """,(
            time_now,
            user_id,
            today
        ))

        conn.commit()

        return "Check-out recorded"

    else:
        return "Attendance already completed"


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

    return render_template("attendance_history.html",data=data)


# -----------------------------
# APPLY LEAVE
# -----------------------------

@app.route("/apply_leave", methods=["GET","POST"])
def apply_leave():

    user_id = session.get("user_id")

    if not user_id:
        return redirect("/")

    if request.method == "POST":

        start_date = request.form["start_date"]
        end_date = request.form["end_date"]
        reason = request.form["reason"]

        conn = get_db()

        conn.execute("""
        INSERT INTO leave_requests
        (user_id,start_date,end_date,reason,status,created_at)
        VALUES (?,?,?,?,?,?)
        """,(
            user_id,
            start_date,
            end_date,
            reason,
            "Pending",
            datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        ))

        conn.commit()

        return "Leave request submitted"

    return render_template("apply_leave.html")


# -----------------------------
# MY LEAVES
# -----------------------------

@app.route("/my_leaves")
def my_leaves():

    user_id = session.get("user_id")

    conn = get_db()

    leaves = conn.execute(
        "SELECT * FROM leave_requests WHERE user_id=?",
        (user_id,)
    ).fetchall()

    return render_template("my_leaves.html",leaves=leaves)


# -----------------------------
# VIEW LEAVE REQUESTS
# -----------------------------

@app.route("/leave_requests")
def leave_requests():

    if session.get("role") not in ["admin","hr"]:
        return redirect("/")

    conn = get_db()

    requests = conn.execute("""
    SELECT leave_requests.*, users.name
    FROM leave_requests
    JOIN users ON users.id = leave_requests.user_id
    """).fetchall()

    return render_template("leave_requests.html",requests=requests)


@app.route("/approve_leave/<int:id>")
def approve_leave(id):

    if session.get("role") not in ["admin","hr"]:
        return redirect("/")

    conn = get_db()

    conn.execute(
        "UPDATE leave_requests SET status='Approved' WHERE id=?",
        (id,)
    )

    conn.commit()

    return redirect("/leave_requests")


@app.route("/reject_leave/<int:id>")
def reject_leave(id):

    if session.get("role") not in ["admin","hr"]:
        return redirect("/")

    conn = get_db()

    conn.execute(
        "UPDATE leave_requests SET status='Rejected' WHERE id=?",
        (id,)
    )

    conn.commit()

    return redirect("/leave_requests")


# -----------------------------
# HOLIDAY MANAGEMENT
# -----------------------------

@app.route("/add_holiday", methods=["GET","POST"])
def add_holiday():

    if session.get("role") != "admin":
        return redirect("/")

    if request.method == "POST":

        name = request.form["name"]
        date = request.form["date"]

        conn = get_db()

        conn.execute(
            "INSERT INTO holidays(name,date) VALUES (?,?)",
            (name,date)
        )

        conn.commit()

        return redirect("/holidays")

    return render_template("add_holiday.html")


@app.route("/holidays")
def holidays():

    conn = get_db()

    data = conn.execute(
        "SELECT * FROM holidays ORDER BY date"
    ).fetchall()

    return render_template("holidays.html",data=data)


# -----------------------------
# VIEW ATTENDANCE (ADMIN)
# -----------------------------

@app.route("/view_attendance")
def view_attendance():

    if session.get("role") not in ["admin","hr"]:
        return redirect("/")

    conn = get_db()

    employee_data = conn.execute("""
    SELECT users.name, attendance.date,
    attendance.check_in_time,
    attendance.check_out_time,
    attendance.status
    FROM attendance
    JOIN users ON users.id = attendance.user_id
    """).fetchall()

    return render_template(
        "view_attendance.html",
        employee_data=employee_data
    )


# -----------------------------
# CALENDAR EVENTS API
# -----------------------------

@app.route("/calendar_events")
def calendar_events():

    user_id = session.get("user_id")

    conn = get_db()

    events = []

    attendance = conn.execute(
        "SELECT date,status FROM attendance WHERE user_id=?",
        (user_id,)
    ).fetchall()

    for r in attendance:

        color = "green"

        if r["status"] == "Late":
            color = "yellow"

        if r["status"] == "Absent":
            color = "red"

        events.append({
            "title": r["status"],
            "start": r["date"],
            "color": color
        })

    holidays = conn.execute(
        "SELECT name,date FROM holidays"
    ).fetchall()

    for h in holidays:

        events.append({
            "title": h["name"],
            "start": h["date"],
            "color": "blue"
        })

    return jsonify(events)


# -----------------------------
# RUN SERVER
# -----------------------------

if __name__ == "__main__":
    app.run(debug=True)

# -----------------------------
# CALENDAR PAGE
# -----------------------------

@app.route("/calendar")
def calendar():

    if not session.get("user_id"):
        return redirect("/")

    return render_template("calendar.html")