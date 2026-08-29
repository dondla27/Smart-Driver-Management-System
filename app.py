from flask import request, jsonify
from gps import save_location
from flask import Flask, render_template, request, redirect, url_for
import mysql.connector
import subprocess

app = Flask(__name__)

# MySQL Database Connection
db = mysql.connector.connect(
    host="localhost",
    user="root",
    password="",      # Change if you have set a MySQL password
    database="smart_driver_db"
)

cursor = db.cursor()

# ---------------- HOME ----------------
@app.route('/')
def home():
    return render_template('index.html')


# ---------------- REGISTER ----------------
@app.route('/register', methods=['GET', 'POST'])
def register():

    if request.method == 'POST':

        name = request.form['name']
        email = request.form['email']
        password = request.form['password']

        sql = "INSERT INTO drivers (name, email, password) VALUES (%s,%s,%s)"
        values = (name, email, password)

        cursor.execute(sql, values)
        db.commit()

        return redirect(url_for('login'))

    return render_template('register.html')


# ---------------- LOGIN ----------------
@app.route('/login', methods=['GET', 'POST'])
def login():

    if request.method == 'POST':

        email = request.form['email']
        password = request.form['password']

        sql = "SELECT * FROM drivers WHERE email=%s AND password=%s"
        cursor.execute(sql, (email, password))

        user = cursor.fetchone()

        if user:
            return redirect(url_for('dashboard'))
        else:
            return "Invalid Email or Password"

    return render_template('login.html')


# ---------------- DASHBOARD ----------------
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
@app.route('/driver_report')
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

# ---------------- START DROWSINESS DETECTION ----------------
@app.route('/start_monitoring')
def start_monitoring():

    subprocess.Popen(["python", "utils/drowsiness.py"])

    return """
    <h2>Drowsiness Detection Started Successfully</h2>

    <a href="/dashboard">
        <button>Back to Dashboard</button>
    </a>
    """


# ---------------- LOGOUT ----------------
@app.route('/logout')
def logout():
    return redirect(url_for('login'))
@app.route('/location')
def location():
    return render_template("location.html")
@app.route("/speed")
def speed():
    return render_template("speed.html")
@app.route('/emergency')
def emergency():
    
    return render_template("emergency.html")






# ---------------- MAIN ----------------

@app.route("/save_location", methods=["POST"])
def save_location_route():

    data = request.get_json()

    latitude = data["latitude"]
    longitude = data["longitude"]

    save_location(latitude, longitude)

    return jsonify({"message": "Location Saved"})
if __name__ == "__main__":
    app.run(debug=True)