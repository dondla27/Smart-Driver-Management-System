import mysql.connector

db = mysql.connector.connect(
    host="localhost",
    user="root",
    password="",
    database="smart_driver_db"
)

cursor = db.cursor()

def save_location(latitude, longitude):
    try:
        sql = "INSERT INTO route_history(latitude, longitude) VALUES(%s,%s)"
        cursor.execute(sql, (latitude, longitude))
        db.commit()
        print("Location Saved:", latitude, longitude)

    except Exception as e:
        print("Database Error:", e)