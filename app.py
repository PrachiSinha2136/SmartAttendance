from flask import Flask, request, jsonify
from flask_cors import CORS
import mysql.connector

app = Flask(__name__)
CORS(app)

def get_db():
    return mysql.connector.connect(
        host="localhost", user="root", password="", database="attendance_system"
    )

# ─── Register Student ───────────────────────────────────────────
@app.route('/save_student', methods=['POST'])
def save_student():
    name        = request.form.get('student_name', '')
    student_id  = request.form.get('student_id', '')
    fingerprint = request.form.get('fingerprint', '')
    image       = request.form.get('image', '')

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO students (student_name, student_id, fingerprint_id, face_encoding) VALUES (%s, %s, %s, %s)",
        (name, student_id, fingerprint, image)
    )
    conn.commit()
    cursor.close()
    conn.close()
    return jsonify({"message": "Student Registered Successfully"})

# ─── Get All Students ────────────────────────────────────────────
@app.route('/get_students', methods=['GET'])
def get_students():
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT id, student_name, student_id, fingerprint_id FROM students")
    students = cursor.fetchall()
    cursor.close()
    conn.close()
    return jsonify(students)

# ─── Mark Attendance ─────────────────────────────────────────────
@app.route('/mark_attendance', methods=['POST'])
def mark_attendance():
    data        = request.json
    student_id  = data.get('student_id')
    fingerprint = data.get('fingerprint')
    face        = data.get('face')  # "captured" string

    conn = get_db()
    cursor = conn.cursor(dictionary=True)

    # Match student by student_id + fingerprint
    cursor.execute(
        "SELECT * FROM students WHERE student_id = %s AND fingerprint_id = %s",
        (student_id, fingerprint)
    )
    student = cursor.fetchone()

    if not student:
        cursor.close()
        conn.close()
        return jsonify({"success": False, "message": "Student not found / fingerprint mismatch"})

    # Save attendance
    cursor.execute(
        "INSERT INTO attendance (student_id, student_name, status, marked_at) VALUES (%s, %s, 'Present', NOW())",
        (student['student_id'], student['student_name'])
    )
    conn.commit()
    cursor.close()
    conn.close()
    return jsonify({"success": True, "message": f"{student['student_name']} ka attendance mark ho gaya!"})

# ─── Get Attendance Records ───────────────────────────────────────
@app.route('/get_attendance', methods=['GET'])
def get_attendance():
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM attendance ORDER BY marked_at DESC")
    records = cursor.fetchall()
    cursor.close()
    conn.close()
    return jsonify(records)

if __name__ == '__main__':
    app.run(debug=True)