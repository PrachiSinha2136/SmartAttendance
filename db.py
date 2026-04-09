import mysql.connector

try:
    db = mysql.connector.connect(
        host="localhost",
        user="root",
        password="",   # XAMPP default blank hota hai
        database="attendance_system"
    )

    if db.is_connected():
        print("Database Connected Successfully!")

except Exception as e:
    print("Error:", e)