from flask import Flask, render_template, request, jsonify, session, redirect, url_for
import sqlite3
from bs4 import BeautifulSoup

app = Flask(__name__)
app.secret_key = "secret-key"


def get_db():
    return sqlite3.connect("courses.db")


def parse_courses():
    # فعلاً نمونه داده تا بعداً از HTML واقعی بخونیم
    return [
        {"name": "ریاضی", "code": "101", "prof": "احمدی", "time": "شنبه 08:00-10:00"},
        {"name": "فیزیک", "code": "102", "prof": "محمدی", "time": "شنبه 10:00-12:00"},
        {"name": "برنامه‌سازی", "code": "103", "prof": "کریمی", "time": "یکشنبه 08:00-10:00"},
    ]


COURSES = parse_courses()


def parse_time(t):
    try:
        day, hours = t.split()
        start, end = hours.split("-")
        return day, start, end
    except:
        return None, None, None


def has_conflict(t1, t2):
    d1, s1, e1 = parse_time(t1)
    d2, s2, e2 = parse_time(t2)

    if d1 != d2:
        return False

    return not (e1 <= s2 or e2 <= s1)


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        session["student"] = request.form["student_id"]
        return redirect(url_for("index"))

    return """
    <form method="post">
        شماره دانشجویی: <input name="student_id">
        <button type="submit">ورود</button>
    </form>
    """


@app.route("/")
def index():
    if "student" not in session:
        return redirect(url_for("login"))
    return render_template("index.html", courses=COURSES)


@app.route("/add", methods=["POST"])
def add_course():
    if "student" not in session:
        return jsonify({"error": "ابتدا وارد شوید"})

    code = request.json["code"]
    course = next(c for c in COURSES if c["code"] == code)

    db = get_db()
    cur = db.cursor()

    cur.execute(
        "CREATE TABLE IF NOT EXISTS picks (student TEXT, code TEXT, time TEXT)"
    )

    cur.execute("SELECT time FROM picks WHERE student=?", (session["student"],))
    for (t,) in cur.fetchall():
        if has_conflict(t, course["time"]):
            return jsonify({"error": "تداخل زمانی وجود دارد"})

    cur.execute(
        "INSERT INTO picks VALUES (?,?,?)",
        (session["student"], code, course["time"]),
    )
    db.commit()

    return jsonify({"success": True})


@app.route("/planner")
def planner():
    if "student" not in session:
        return redirect(url_for("login"))

    db = get_db()
    cur = db.cursor()
    cur.execute(
        "SELECT code, time FROM picks WHERE student=?", (session["student"],)
    )
    picks = cur.fetchall()

    selected = [c for c in COURSES if any(p[0] == c["code"] for p in picks)]

    return render_template("planner.html", courses=selected)


if __name__ == "__main__":
    app.run()
