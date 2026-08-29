import mysql.connector

db = mysql.connector.connect(
    host="localhost",
    user="root",
    password="",
    database="smart_driver_db"
)

cursor = db.cursor()