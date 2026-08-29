from flask import Flask, render_template, request, redirect, url_for, session, flash
import mysql.connector

app = Flask(__name__)
app.secret_key = "smart_driver_secret"

# Database Connection
db = mysql.connector.connect(
    host="localhost",
    user="root",
    password="",          # Change if your MySQL has a password
    database="smart_driver_db"
)

cursor = db.cursor()

# Home Page
@app.route('/')
def home():
    return render_template('index.html')


# Registration
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        phone = request.form['phone']
        password = request.form['password']
        license_number = request.form['license_number']
        vehicle_number = request.form['vehicle_number']

        sql = """
        INSERT INTO drivers
        (name,email,phone,password,license_number,vehicle_number)
        VALUES (%s,%s,%s,%s,%s,%s)
        """

        values = (
            name,
            email,
            phone,
            password,
            license_number,
            vehicle_number
        )

        cursor.execute(sql, values)
        db.commit()

        flash("Registration Successful!")
        return redirect(url_for('login'))

    return render_template("register.html")


# Login
@app.route('/login', methods=['GET', 'POST'])
def login():

    if request.method == 'POST':

        email = request.form['email']
        password = request.form['password']

        sql = "SELECT * FROM drivers WHERE email=%s AND password=%s"
        cursor.execute(sql, (email, password))

        user = cursor.fetchone()

        if user:
            session['user'] = user[1]
            return redirect(url_for('dashboard'))

        else:
            flash("Invalid Email or Password")

    return render_template("login.html")


# Dashboard
@app.route('/dashboard')
def dashboard():

    if 'user' not in session:
        return redirect(url_for('login'))

    return render_template("dashboard.html", username=session['user'])


# Logout
@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('login'))


if __name__ == "__main__":
    app.run(debug=True)