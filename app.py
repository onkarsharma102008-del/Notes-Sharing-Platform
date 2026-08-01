from flask import Flask, render_template, request, redirect, url_for, session, send_from_directory 
from flask_mail import Mail, Message
import random
from datetime import datetime
from flask import send_from_directory
from smtplib import SMTPRecipientsRefused
import sqlite3
import os
from dotenv import load_dotenv
load_dotenv()
from werkzeug.utils import secure_filename


app = Flask(__name__)
app.secret_key =os.getenv("SECRET_KEY")
app.config["MAIL_SERVER"] = "smtp.gmail.com"
app.config["MAIL_PORT"] = 587
app.config["MAIL_USE_TLS"] = True
app.config["MAIL_USERNAME"] = os.getenv("MAIL_USERNAME")
app.config["MAIL_PASSWORD"] = os.getenv("MAIL_PASSWORD")
resend.api_key = os.getenv("Resend_API_KEY")

conn = sqlite3.connect("users.db")
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS notes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT,
    subject TEXT,
    course TEXT
    semester TEXT,
    filename TEXT,
    Uploaded_by TEXT,
    upload_date TEXT
)
""")

conn.commit()
conn.close()




UPLOAD_FOLDER = "uploads"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

import os

if not os.path.exists(app.config["UPLOAD_FOLDER"]):
    os.makedirs(app.config["UPLOAD_FOLDER"])

conn = sqlite3.connect("users.db")
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS notes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT,
    subject TEXT,
    semester TEXT,
    filename TEXT,
    Uploaded_by TEXT,
    upload_date TEXT
)
""")

conn.commit()
conn.close()

@app.route("/")
def home():
    return render_template("index.html")


@app.route("/signup", methods=["GET", "POST"])
def signup():

    if request.method == "POST":
        fullname = request.form.get("fullname")
        email = request.form.get("email")
        username = request.form.get("username")
        password = request.form.get("password")

        # Session me user data save karo
        session["fullname"] = fullname
        session["email"] = email
        session["username"] = username
        session["password"] = password

        # OTP generate
        otp = str(random.randint(100000, 999999))
        session["otp"] = otp

        msg = Message(
            "Email Verification",
            sender=app.config["MAIL_USERNAME"],
            recipients=[email]
        )

        msg.body = f"Your OTP is: {otp}"

        try:
            mail.send(msg)
            return redirect(url_for("verify_otp"))

        except SMTPRecipientsRefused:
            return render_template(
                "signup.html",
                error="This email is not available."
            )

    return render_template("signup.html")

@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        print(request.form)

        email = request.form["email"]
        password = request.form["password"]

        print("Email:",email)
        print("password:",password)
        
        conn = sqlite3.connect("users.db")
        cursor = conn.cursor()

        cursor.execute(
            "SELECT * FROM users WHERE email=? AND password=?",
            (email, password)
        )

        user = cursor.fetchone()
        conn.close()

        if user:

            session["username"] = user[3]
            

            msg = Message(
                "Login Successful",
                sender=app.config["MAIL_USERNAME"],
                recipients=[email]
            )

            msg.body = """
Hello,

Your account has been logged in successfully.

If this was not you, please change your password immediately.

Thank you,
Notes Sharing Platform.
"""

            mail.send(msg)
            return redirect(url_for("dashboard"))

        else:
            return "Invalid Email or Password"

    return render_template("login.html")


@app.route("/dashboard")
def dashboard():

    if "username" not in session: 
        return redirect(url_for("login"))

    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM notes")
    total_notes = cursor.fetchone()[0]

    conn.close()

    return render_template(
        "dashboard.html",
        total_notes=total_notes
    )

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

@app.route("/upload", methods=["GET", "POST"])
def upload():

    if "username" not in session:
        return redirect(url_for("login"))

    if request.method == "POST":

        conn = sqlite3.connect("users.db")
        cursor = conn.cursor()

        title = request.form["title"]
        course = request.form["course"]
        # subject = request.form["subject"]
        semester = request.form["semester"]

        # Course ke hisab se Subject set hoga
        if course == "B.Tech":
            subject = "Computer Science"
        elif course == "BCA":
            subject = "Computer Science"
        elif course == "B.Pharma":
            subject = "Pharmacy"
        elif course == "B.Com":
            subject = "Commerce"
        else:
            subject = "General"

        uploaded_by = session["username"]
        upload_date = datetime.now().strftime("%d-%m-%Y")

        file = request.files["pdf"]
        filename = secure_filename(file.filename)
        file.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))

        cursor.execute("""
            INSERT INTO notes
            (title, subject, semester, filename, uploaded_by, upload_date, course)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            title,
            subject,
            semester,
            filename,
            uploaded_by,
            upload_date,
            course
        ))

        conn.commit()
        conn.close()

        return redirect(url_for("notes"))

    return render_template("upload.html")

   
@app.route("/notes")
def notes():
    if "username" not in session:
        return redirect(url_for("login"))

    search = request.args.get("search", "")

    conn = sqlite3.connect("users.db")
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    if search:
        cursor.execute("""
            SELECT * FROM notes
            WHERE title LIKE ? OR subject LIKE ?
        """, (f"%{search}%", f"%{search}%"))
    else:
        cursor.execute("SELECT * FROM notes")

    notes = cursor.fetchall()
    conn.close()

    return render_template("all_notes.html", notes=notes)

@app.route("/profile")
def profile():

    if "username" not in session:
        return redirect(url_for("login"))

    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()

    cursor.execute(
        "SELECT fullname, username, email FROM users WHERE username=?",
        (session["username"],)
    )
    user = cursor.fetchone()

    cursor.execute(
        "SELECT id,title,subject,semester,upload_date FROM notes WHERE uploaded_by=?",
        (session["username"],)
    )
    notes = cursor.fetchall()

    conn.close()

    return render_template("profile.html", user=user, notes=notes)


@app.route("/edit-profile", methods=["GET", "POST"])
def edit_profile():

    conn = sqlite3.connect("users.db")
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    username = session["username"]

    cursor.execute("SELECT * FROM users WHERE username=?", (username,))
    user = cursor.fetchone()

    if request.method == "POST":
        fullname = request.form["fullname"]
        email = request.form["email"]
        new_username = request.form["username"]

        cursor.execute("""
            UPDATE users
            SET fullname=?, email=?, username=?
            WHERE username=?
        """, (fullname, email, new_username, username))

        conn.commit()
        conn.close()

        session["username"] = new_username
        return redirect(url_for("profile"))

    conn.close()
    return render_template("edit_profile.html", user=user)


@app.route("/all-notes")
def all_notes():

     if "username" not in session:
        return redirect(url_for("login"))

     conn = sqlite3.connect("users.db")
     conn.row_factory = sqlite3.Row
     cursor = conn.cursor()

     cursor.execute("""
    SELECT id,
           title,
           subject,
           semester,
           filename,
           uploaded_by,
           upload_date
    FROM notes
    """)

     notes = cursor.fetchall()

     conn.close()

     return render_template("all_notes.html", notes=notes)


@app.route("/change-password", methods=["GET", "POST"])
def change_password():

    if "username" not in session:
        return redirect(url_for("login"))

    if request.method == "POST":
        current_password = request.form["old_password"]
        new_password = request.form["new_password"]
        confirm_password = request.form["confirm_password"]

        if new_password != confirm_password:
            return "New Password and Confirm Password do not match."

        conn = sqlite3.connect("users.db")
        cursor = conn.cursor()

        cursor.execute(
            "SELECT password FROM users WHERE username=?",
            (session["username"],)
        )
        user = cursor.fetchone()

        if not user:
            conn.close()
            return "User not found."

        if user[0] != current_password:
            conn.close()
            return "Current Password is incorrect."

        cursor.execute(
            "UPDATE users SET password=? WHERE username=?",
            (new_password, session["username"])
        )
        conn.commit()
        conn.close()

        return "Password changed successfully."

    return render_template("change_password.html")

@app.route("/download/<filename>")
def download(filename):
    return send_from_directory("uploads", filename, as_attachment=True)

@app.route("/download-notes")
def download_notes():

    conn = sqlite3.connect("users.db")
    conn.row_factory = sqlite3.Row

    cursor = conn.cursor()
    cursor.execute("SELECT * FROM notes")

    notes = cursor.fetchall()

    conn.close()

    return render_template("download_notes.html", notes=notes)

@app.route("/edit/<int:id>", methods=["GET", "POST"])
def edit(id):

    conn = sqlite3.connect("users.db")
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM notes WHERE id=?", (id,))
    note = cursor.fetchone()

    if request.method == "POST":
        title = request.form["title"]
        subject = request.form["subject"]
        semester = request.form["semester"]

        cursor.execute("""
            UPDATE notes
            SET title=?, subject=?, semester=?
            WHERE id=?
        """, (title,subject, semester, id))

        conn.commit()
        conn.close()

        return redirect(url_for("notes"))

    conn.close()
    return render_template("edit_notes.html", note=note)

@app.route("/delete/<int:id>")
def delete(id):
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()

    cursor.execute("DELETE FROM notes WHERE id = ?", (id,))
    conn.commit()
    conn.close()

    return redirect(url_for("notes"))


@app.route("/preview/<filename>")
def preview_file(filename):
    return send_from_directory(
        "uploads",
        filename,
        as_attachment=False
    )

@app.route("/forgot_password", methods=["GET", "POST"])
def forgot_password():

    if request.method == "POST":

        email = request.form["email"]

        conn = sqlite3.connect("users.db")
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM users WHERE email=?", (email,))
        user = cursor.fetchone()

        conn.close()

        if user:

            otp = str(random.randint(100000, 999999))

            session["reset_email"] = email
            session["reset_otp"] = otp

            msg = Message(
                "Password Reset OTP",
                sender=app.config["MAIL_USERNAME"],
                recipients=[email]
            )

            msg.body = f"Your Password Reset OTP is: {otp}"

            mail.send(msg)

            return redirect(url_for("verify_reset_otp"))

        else:
            return "Email not found."

    return render_template("forgot_password.html")

@app.route("/reset_password", methods=["GET", "POST"])
def reset_password():
    email = session.get("reset_email")

    if request.method == "POST":
        new_password = request.form["new_password"]

        conn = sqlite3.connect("users.db")
        cursor = conn.cursor()

        cursor.execute(
            "UPDATE users SET password=? WHERE email=?",
            (new_password, email)
        )

        conn.commit()
        conn.close()

        session.pop("reset_email", None)
        session.pop("reset_otp", None)

        return redirect(url_for("login"))

    return render_template("reset_password.html") 

@app.route("/verify_otp", methods=["GET", "POST"])
def verify_otp():
    if request.method == "POST":
        entered_otp = request.form["otp"]

        if entered_otp == session.get("otp"):

            # Yahan user ko database me save karo
            conn = sqlite3.connect("users.db")
            cursor = conn.cursor()

            cursor.execute("""
                INSERT INTO users(fullname, email, username, password)
                VALUES (?, ?, ?, ?)
            """, (
                session["fullname"],
                session["email"],
                session["username"],
                session["password"],
            ))

            conn.commit()
            conn.close()

            session.pop("otp", None)

            return redirect(url_for("login"))   # 👈 OTP ke baad Login page

        else:
            return "Invalid OTP"

    return render_template("verify_otp.html")

@app.route("/verify_reset_otp", methods=["GET", "POST"])
def verify_reset_otp():

    if request.method == "POST":

        otp = request.form["otp"]

        if otp == session.get("reset_otp"):
            return redirect(url_for("reset_password"))
        else:
            return "Invalid OTP"

    return render_template("verify_reset_otp.html")

@app.route("/course/<course_name>")
def course_notes(course_name):

    if "username" not in session:
        return redirect(url_for("login"))

    conn = sqlite3.connect("users.db")
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute(
        "SELECT * FROM notes WHERE course=?",
        (course_name,)
    )

    notes = cursor.fetchall()
    conn.close()

    return render_template("all_notes.html", notes=notes)

def init_db():
    conn = sqlite3.connect("users.db")
    c = conn.cursor()

    c.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        fullname TEXT,
        email TEXT,
        username TEXT,
        password TEXT
    )
    """)

    conn.commit()
    conn.close()

init_db()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
