from flask import Flask, render_template, request, redirect, url_for, session, send_from_directory 
from flask_mail import Mail, Message
from datetime import datetime
import sqlite3
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)

app.config["MAIL_SERVER"] = "smtp.gmail.com"
app.config["MAIL_PORT"] = 587
app.config["MAIL_USE_TLS"] = True
app.config["MAIL_USERNAME"] = "yourgmail@gmail.com"
app.config["MAIL_PASSWORD"] = "your_app_password"

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

app.secret_key = "my_secret_key"


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

        if not fullname or not email or not username or not password:
            return "Please fill all fields."

        # Database me save karne ka code

    return render_template("signup.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        if not username or not password:
            return "Please fill all fields."

        # Login check
        conn = sqlite3.connect("users.db")
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM users WHERE username=? AND password=?",
            (username, password)
        )
        user = cursor.fetchone()
        conn.close()

        if user:
            session["username"] = username
            return redirect(url_for("dashboard"))
        else:
            return "Invalid Username or Password"

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

        title = request.form["title"]
        subject = request.form["subject"]
        semester = request.form["semester"]
        Uploaded_by = session["username"]
        upload_date = datetime.now().strftime("%d %b %y")

        file = request.files["pdf"]
        filename =  secure_filename (file.filename)
        file.save(os.path.join(app.config["UPLOAD_FOLDER"],filename))
        upload_date = datetime.now().strftime("%d-%m-%Y")

        conn = sqlite3.connect("users.db")
        cursor = conn.cursor()

        cursor.execute("""
        INSERT INTO notes
        (title, subject, semester, filename, uploaded_by)
        VALUES (?, ?, ?, ?, ?)
        """, (
            title,
            subject,
            semester,
            filename,
            Uploaded_by
        ))

        conn.commit()
        conn.close()

        return redirect(url_for("notes"))

     return render_template("upload.html")

   
@app.route("/notes")
def notes():

    if "username" not in session:
        return redirect(url_for("login"))

    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()

    cursor.execute("""
    SELECT id, title, subject, semester, uploaded_by
    FROM notes
    WHERE uploaded_by = ?
    """, (session["username"],))

    notes = cursor.fetchall()

    conn.close()

    return render_template("notes.html", notes=notes)

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
        "SELECT id,title,subject,semester FROM notes WHERE uploaded_by=?",
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
        """, (title, subject, semester, id))

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

if __name__ == "__main__":
    app.run(debug=True)


