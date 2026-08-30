from flask import Flask, render_template, request, redirect, url_for, jsonify
import mysql.connector
import os
import sys
import subprocess

app = Flask(__name__)


# =========================================================
# DATABASE CONNECTION
# =========================================================

def get_db_connection():
    return mysql.connector.connect(
        host=os.environ.get("DB_HOST", "localhost"),
        user=os.environ.get("DB_USER", "root"),
        password=os.environ.get("DB_PASSWORD", ""),
        database=os.environ.get("DB_NAME", "smart_driver_db"),
        port=int(os.environ.get("DB_PORT", "3306"))
    )


# =========================================================
# HOME
# =========================================================

@app.route("/")
def home():
    return render_template("index.html")


# =========================================================
# REGISTER
# =========================================================

@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        name = request.form["name"]
        email = request.form["email"]
        password = request.form["password"]

        try:
            db = get_db_connection()
            cursor = db.cursor()

            sql = """
                INSERT INTO drivers (name, email, password)
                VALUES (%s, %s, %s)
            """

            cursor.execute(sql, (name, email, password))
            db.commit()

            cursor.close()
            db.close()

            return redirect(url_for("login"))

        except Exception as e:
            return f"Registration Error: {e}"

    return render_template("register.html")


# =========================================================
# LOGIN
# =========================================================

@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        email = request.form["email"]
        password = request.form["password"]

        try:
            db = get_db_connection()
            cursor = db.cursor()

            sql = """
                SELECT * FROM drivers
                WHERE email=%s AND password=%s
            """

            cursor.execute(sql, (email, password))
            user = cursor.fetchone()

            cursor.close()
            db.close()

            if user:
                return redirect(url_for("dashboard"))

            return "Invalid Email or Password"

        except Exception as e:
            return f"Login Error: {e}"

    return render_template("login.html")


# =========================================================
# DASHBOARD
# =========================================================

@app.route("/dashboard")
def dashboard():

    return render_template(
        "dashboard.html",
        driver_name="Prasanna",
        score=92,
        status="SAFE DRIVER",
        drowsiness=2,
        yawn=3,
        phone=1,
        head=2,
        emergency=0,
        driving_time="02:15:20",
        gps="Active"
    )


# =========================================================
# DRIVER REPORT
# =========================================================

@app.route("/driver_report")
def driver_report():

    return render_template(
        "driver_report.html",
        driver_name="Prasanna",
        score=92,
        driving_time="02:15:30",
        drowsiness=2,
        yawn=3,
        phone=1,
        head=2,
        emergency=0,
        latitude="13.6089",
        longitude="78.5023"
    )


# =========================================================
# START DROWSINESS DETECTION
# =========================================================

@app.route("/start_monitoring")
def start_monitoring():

    try:
        subprocess.Popen(
            [sys.executable, "utils/drowsiness.py"]
        )

        return """
        <h2>Drowsiness Detection Started Successfully</h2>
        <a href="/dashboard">
            <button>Back to Dashboard</button>
        </a>
        """

    except Exception as e:
        return f"Error starting drowsiness detection: {e}"


# =========================================================
# START HEAD POSE DETECTION
# =========================================================

@app.route("/start_headpose")
def start_headpose():

    try:
        subprocess.Popen(
            [sys.executable, "utils/head_pose.py"]
        )

        return """
        <h2>Head Pose Detection Started Successfully</h2>
        <a href="/dashboard">
            <button>Back to Dashboard</button>
        </a>
        """

    except Exception as e:
        return f"Error starting head pose detection: {e}"


# =========================================================
# START PHONE DETECTION
# =========================================================

@app.route("/start_phone")
def start_phone():

    try:
        subprocess.Popen(
            [sys.executable, "utils/phone_detection.py"]
        )

        return """
        <h2>Phone Detection Started Successfully</h2>
        <a href="/dashboard">
            <button>Back to Dashboard</button>
        </a>
        """

    except Exception as e:
        return f"Error starting phone detection: {e}"


# =========================================================
# START YAWN DETECTION
# =========================================================

@app.route("/start_yawn")
def start_yawn():

    try:
        subprocess.Popen(
            [sys.executable, "utils/yawn.py"]
        )

        return """
        <h2>Yawn Detection Started Successfully</h2>
        <a href="/dashboard">
            <button>Back to Dashboard</button>
        </a>
        """

    except Exception as e:
        return f"Error starting yawn detection: {e}"


# =========================================================
# LOCATION PAGE
# =========================================================

@app.route("/location")
def location():
    return render_template("location.html")


# =========================================================
# SPEED PAGE
# =========================================================

@app.route("/speed")
def speed():
    return render_template("speed.html")


# =========================================================
# EMERGENCY PAGE
# =========================================================

@app.route("/emergency")
def emergency():
    return render_template("emergency.html")


# =========================================================
# SAVE GPS LOCATION
# =========================================================

@app.route("/save_location", methods=["POST"])
def save_location_route():

    try:

        data = request.get_json()

        latitude = data.get("latitude")
        longitude = data.get("longitude")

        if latitude is None or longitude is None:
            return jsonify({
                "success": False,
                "message": "Latitude and longitude are required"
            }), 400

        db = get_db_connection()
        cursor = db.cursor()

        # Make sure this table exists in your database.
        sql = """
            INSERT INTO locations (latitude, longitude)
            VALUES (%s, %s)
        """

        cursor.execute(sql, (latitude, longitude))
        db.commit()

        cursor.close()
        db.close()

        return jsonify({
            "success": True,
            "message": "Location Saved"
        })

    except Exception as e:

        return jsonify({
            "success": False,
            "message": str(e)
        }), 500


# =========================================================
# LOGOUT
# =========================================================

@app.route("/logout")
def logout():
    return redirect(url_for("login"))


# =========================================================
# HEALTH CHECK
# =========================================================

@app.route("/health")
def health():
    return jsonify({
        "status": "Smart Driver Management System is running"
    })


# =========================================================
# MAIN
# =========================================================

if __name__ == "__main__":

    port = int(os.environ.get("PORT", 5000))

    app.run(
        host="0.0.0.0",
        port=port,
        debug=False
    )