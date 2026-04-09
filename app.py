import os
import csv
import io
from datetime import date, datetime, timedelta
from functools import wraps

import psycopg2
import psycopg2.extras
from flask import (Flask, render_template, request, redirect, url_for,
                   session, jsonify, flash, Response, make_response)
from werkzeug.security import generate_password_hash, check_password_hash
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import (SimpleDocTemplate, Table, TableStyle,
                                Paragraph, Spacer)

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-prod')

DATABASE_URL = os.environ.get(
    'DATABASE_URL',
    'postgresql://admin:smartpass123@localhost:5432/attendance_system'
)


# ─── DB helpers ──────────────────────────────────────────────────────────────

def get_db():
    return psycopg2.connect(DATABASE_URL)


def query(sql, params=(), one=False):
    with get_db() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(sql, params)
            return (cur.fetchone() if one else cur.fetchall())


def execute(sql, params=()):
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, params)
        conn.commit()


# ─── Auth decorator ──────────────────────────────────────────────────────────

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'teacher_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated


# ─── Auth routes ─────────────────────────────────────────────────────────────

@app.route('/')
def index():
    if 'teacher_id' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        teacher = query('SELECT * FROM teachers WHERE email = %s', (email,), one=True)
        if teacher and check_password_hash(teacher['password_hash'], password):
            session['teacher_id'] = teacher['id']
            session['teacher_name'] = teacher['name']
            return redirect(url_for('dashboard'))
        flash('Invalid email or password', 'error')
    return render_template('login.html')


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))


# ─── Dashboard ───────────────────────────────────────────────────────────────

@app.route('/dashboard')
@login_required
def dashboard():
    today = date.today().isoformat()
    month = request.args.get('month', date.today().strftime('%Y-%m'))
    class_filter = request.args.get('class_name', '')
    search = request.args.get('search', '')

    total_students = query('SELECT COUNT(*) AS c FROM students', one=True)['c']
    today_present = query(
        "SELECT COUNT(*) AS c FROM attendance WHERE date = %s AND status = 'Present'",
        (today,), one=True
    )['c']

    sql = """
        SELECT s.student_id, s.name, s.class_name,
               COUNT(a.id) AS total_days,
               SUM(CASE WHEN a.status='Present' THEN 1 ELSE 0 END) AS present_days
        FROM students s
        LEFT JOIN attendance a ON s.student_id = a.student_id
            AND TO_CHAR(a.date, 'YYYY-MM') = %s
        WHERE 1=1
    """
    params = [month]
    if class_filter:
        sql += " AND s.class_name = %s"
        params.append(class_filter)
    if search:
        sql += " AND (s.name ILIKE %s OR s.student_id ILIKE %s)"
        params += ['%' + search + '%', '%' + search + '%']
    sql += " GROUP BY s.student_id, s.name, s.class_name ORDER BY s.name"
    students = query(sql, params)

    avg_pct = 0
    low_count = 0
    for st in students:
        if st['total_days'] and st['total_days'] > 0:
            pct = ((st['present_days'] or 0) / st['total_days']) * 100
            avg_pct += pct
            if pct < 75:
                low_count += 1
    avg_pct = round(avg_pct / len(students), 1) if students else 0

    weeks = ['Week 1', 'Week 2', 'Week 3', 'Week 4']
    weekly_present = []
    weekly_pct = []
    for i in range(4):
        day_start = 1 + i * 7
        day_end = day_start + 6
        r1 = query("""
            SELECT COUNT(*) AS c FROM attendance
            WHERE TO_CHAR(date,'YYYY-MM') = %s
              AND EXTRACT(DAY FROM date) BETWEEN %s AND %s
              AND status = 'Present'
        """, (month, day_start, day_end), one=True)
        r2 = query("""
            SELECT COUNT(*) AS c FROM attendance
            WHERE TO_CHAR(date,'YYYY-MM') = %s
              AND EXTRACT(DAY FROM date) BETWEEN %s AND %s
        """, (month, day_start, day_end), one=True)
        present = r1['c'] if r1 else 0
        total = r2['c'] if r2 else 0
        weekly_present.append(present)
        weekly_pct.append(round((present / total * 100) if total else 0, 1))

    classes = [r['class_name'] for r in query(
        'SELECT DISTINCT class_name FROM students ORDER BY class_name')]

    return render_template('dashboard.html',
                           total_students=total_students,
                           today_present=today_present,
                           avg_pct=avg_pct,
                           low_count=low_count,
                           students=students,
                           weeks=weeks,
                           weekly_present=weekly_present,
                           weekly_pct=weekly_pct,
                           month=month,
                           class_filter=class_filter,
                           search=search,
                           classes=classes)


# ─── Register Student ─────────────────────────────────────────────────────────

@app.route('/register')
@login_required
def register():
    classes = [r['class_name'] for r in query(
        'SELECT DISTINCT class_name FROM students ORDER BY class_name')]
    return render_template('register.html', classes=classes)


@app.route('/api/students', methods=['POST'])
@login_required
def save_student():
    data = request.get_json() or request.form
    student_id = (data.get('student_id') or '').strip()
    name = (data.get('name') or '').strip()
    email = (data.get('email') or '').strip()
    class_name = (data.get('class_name') or 'General').strip()
    fingerprint_id = (data.get('fingerprint_id') or '').strip()
    face_encoding = (data.get('face_encoding') or '').strip()

    if not student_id or not name:
        return jsonify({'success': False, 'message': 'Student ID and Name are required'}), 400

    existing = query('SELECT id FROM students WHERE student_id = %s', (student_id,), one=True)
    if existing:
        return jsonify({'success': False, 'message': 'Student ID already exists'}), 409

    execute("""
        INSERT INTO students (student_id, name, email, class_name, fingerprint_id, face_encoding)
        VALUES (%s, %s, %s, %s, %s, %s)
    """, (student_id, name, email, class_name, fingerprint_id, face_encoding))
    return jsonify({'success': True, 'message': 'Student ' + name + ' registered successfully'})


@app.route('/api/students', methods=['GET'])
@login_required
def get_students():
    students = query('SELECT id, student_id, name, email, class_name, fingerprint_id, registered_at FROM students ORDER BY name')
    return jsonify([dict(s) for s in students])


@app.route('/api/students/lookup', methods=['GET'])
@login_required
def lookup_student():
    student_id = request.args.get('student_id', '').strip()
    fingerprint_id = request.args.get('fingerprint_id', '').strip()
    if fingerprint_id:
        student = query('SELECT student_id, name FROM students WHERE fingerprint_id = %s',
                        (fingerprint_id,), one=True)
    elif student_id:
        student = query('SELECT student_id, name FROM students WHERE student_id = %s',
                        (student_id,), one=True)
    else:
        return jsonify({'found': False})
    if student:
        return jsonify({'found': True, 'student_id': student['student_id'], 'name': student['name']})
    return jsonify({'found': False})


# ─── Mark Attendance ─────────────────────────────────────────────────────────

@app.route('/attendance')
@login_required
def attendance():
    students = query('SELECT student_id, name, class_name FROM students ORDER BY name')
    today = date.today().isoformat()
    today_records = query("""
        SELECT a.student_id, s.name, s.class_name, a.status, a.method,
               TO_CHAR(a.marked_at, 'HH12:MI AM') AS time
        FROM attendance a JOIN students s ON a.student_id = s.student_id
        WHERE a.date = %s ORDER BY a.marked_at DESC
    """, (today,))
    return render_template('attendance.html',
                           students=students,
                           today_records=today_records,
                           today=today)


@app.route('/api/attendance', methods=['POST'])
@login_required
def mark_attendance():
    data = request.get_json() or {}
    student_id = (data.get('student_id') or '').strip()
    status = data.get('status', 'Present')
    method = data.get('method', 'manual')
    att_date = data.get('date', date.today().isoformat())

    if not student_id:
        return jsonify({'success': False, 'message': 'Student ID required'}), 400

    student = query('SELECT * FROM students WHERE student_id = %s', (student_id,), one=True)
    if not student:
        return jsonify({'success': False, 'message': 'Student not found'}), 404

    if method == 'fingerprint':
        fp = (data.get('fingerprint_id') or '').strip()
        if fp != student['fingerprint_id']:
            return jsonify({'success': False, 'message': 'Fingerprint mismatch'}), 401

    execute("""
        INSERT INTO attendance (student_id, date, status, method)
        VALUES (%s, %s, %s, %s)
        ON CONFLICT (student_id, date)
        DO UPDATE SET status=EXCLUDED.status, method=EXCLUDED.method, marked_at=NOW()
    """, (student_id, att_date, status, method))
    return jsonify({'success': True,
                    'message': student['name'] + "'s attendance marked as " + status})


@app.route('/api/attendance', methods=['GET'])
@login_required
def get_attendance():
    att_date = request.args.get('date', date.today().isoformat())
    records = query("""
        SELECT a.student_id, s.name, s.class_name, a.status, a.method,
               TO_CHAR(a.marked_at, 'HH12:MI AM') AS time
        FROM attendance a JOIN students s ON a.student_id = s.student_id
        WHERE a.date = %s ORDER BY a.marked_at DESC
    """, (att_date,))
    return jsonify([dict(r) for r in records])


# ─── Per-student detail ───────────────────────────────────────────────────────

@app.route('/students/<student_id>')
@login_required
def student_detail(student_id):
    student = query('SELECT * FROM students WHERE student_id = %s', (student_id,), one=True)
    if not student:
        flash('Student not found', 'error')
        return redirect(url_for('dashboard'))

    records = query("""
        SELECT date, status, method, TO_CHAR(marked_at, 'HH12:MI AM') AS time
        FROM attendance WHERE student_id = %s ORDER BY date DESC
    """, (student_id,))

    total = len(records)
    present = sum(1 for r in records if r['status'] == 'Present')
    absent = total - present
    pct = round((present / total * 100) if total else 0, 1)

    months = []
    month_pcts = []
    for i in range(5, -1, -1):
        d = date.today().replace(day=1) - timedelta(days=i * 28)
        m = d.strftime('%Y-%m')
        label = d.strftime('%b %Y')
        row = query("""
            SELECT COUNT(*) AS total,
                   SUM(CASE WHEN status='Present' THEN 1 ELSE 0 END) AS present
            FROM attendance WHERE student_id = %s AND TO_CHAR(date,'YYYY-MM') = %s
        """, (student_id, m), one=True)
        p = round(((row['present'] or 0) / row['total'] * 100) if row and row['total'] else 0, 1)
        months.append(label)
        month_pcts.append(p)

    return render_template('student_detail.html',
                           student=student,
                           records=records,
                           total=total,
                           present=present,
                           absent=absent,
                           pct=pct,
                           months=months,
                           month_pcts=month_pcts)


# ─── Reports ─────────────────────────────────────────────────────────────────

@app.route('/reports')
@login_required
def reports():
    month = request.args.get('month', date.today().strftime('%Y-%m'))
    class_filter = request.args.get('class_name', '')
    search = request.args.get('search', '')

    sql = """
        SELECT s.student_id, s.name, s.class_name,
               COUNT(a.id) AS total_days,
               SUM(CASE WHEN a.status='Present' THEN 1 ELSE 0 END) AS present_days
        FROM students s
        LEFT JOIN attendance a ON s.student_id = a.student_id
            AND TO_CHAR(a.date, 'YYYY-MM') = %s
        WHERE 1=1
    """
    params = [month]
    if class_filter:
        sql += " AND s.class_name = %s"
        params.append(class_filter)
    if search:
        sql += " AND (s.name ILIKE %s OR s.student_id ILIKE %s)"
        params += ['%' + search + '%', '%' + search + '%']
    sql += " GROUP BY s.student_id, s.name, s.class_name ORDER BY s.name"
    students = query(sql, params)

    rows = []
    for st in students:
        t = st['total_days'] or 0
        p = st['present_days'] or 0
        pct = round((p / t * 100) if t else 0, 1)
        rows.append({**dict(st), 'pct': pct,
                     'absent_days': t - p,
                     'status_label': 'Excellent' if pct >= 85 else ('Good' if pct >= 75 else 'Low')})

    avg_pct = round(sum(r['pct'] for r in rows) / len(rows), 1) if rows else 0

    months_labels = []
    months_pcts = []
    for i in range(5, -1, -1):
        d = date.today().replace(day=1) - timedelta(days=i * 28)
        m = d.strftime('%Y-%m')
        label = d.strftime('%b %Y')
        row = query("""
            SELECT COUNT(*) AS total,
                   SUM(CASE WHEN status='Present' THEN 1 ELSE 0 END) AS present
            FROM attendance WHERE TO_CHAR(date,'YYYY-MM') = %s
        """, (m,), one=True)
        p = round(((row['present'] or 0) / row['total'] * 100) if row and row['total'] else 0, 1)
        months_labels.append(label)
        months_pcts.append(p)

    classes = [r['class_name'] for r in query(
        'SELECT DISTINCT class_name FROM students ORDER BY class_name')]

    return render_template('reports.html',
                           rows=rows,
                           month=month,
                           avg_pct=avg_pct,
                           class_filter=class_filter,
                           search=search,
                           classes=classes,
                           months_labels=months_labels,
                           months_pcts=months_pcts)


# ─── Download CSV ─────────────────────────────────────────────────────────────

@app.route('/api/download/csv')
@login_required
def download_csv():
    month = request.args.get('month', date.today().strftime('%Y-%m'))
    student_id = request.args.get('student_id', '')

    if student_id:
        rows = query("""
            SELECT s.student_id, s.name, s.class_name, a.date, a.status, a.method
            FROM attendance a JOIN students s ON a.student_id = s.student_id
            WHERE a.student_id = %s ORDER BY a.date
        """, (student_id,))
        filename = 'attendance_' + student_id + '.csv'
    else:
        rows = query("""
            SELECT s.student_id, s.name, s.class_name, a.date, a.status, a.method
            FROM attendance a JOIN students s ON a.student_id = s.student_id
            WHERE TO_CHAR(a.date,'YYYY-MM') = %s ORDER BY s.name, a.date
        """, (month,))
        filename = 'attendance_' + month + '.csv'

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['Student ID', 'Name', 'Class', 'Date', 'Status', 'Method'])
    for r in rows:
        writer.writerow([r['student_id'], r['name'], r['class_name'],
                         r['date'], r['status'], r['method']])

    return Response(
        output.getvalue(),
        mimetype='text/csv',
        headers={'Content-Disposition': 'attachment; filename=' + filename}
    )


# ─── Download PDF ─────────────────────────────────────────────────────────────

@app.route('/api/download/pdf')
@login_required
def download_pdf():
    month = request.args.get('month', date.today().strftime('%Y-%m'))
    student_id = request.args.get('student_id', '')

    if student_id:
        rows = query("""
            SELECT s.student_id, s.name, s.class_name,
                   COUNT(a.id) AS total_days,
                   SUM(CASE WHEN a.status='Present' THEN 1 ELSE 0 END) AS present_days
            FROM students s
            LEFT JOIN attendance a ON s.student_id = a.student_id
            WHERE s.student_id = %s
            GROUP BY s.student_id, s.name, s.class_name
        """, (student_id,))
        title = 'Attendance Report - Student ' + student_id
        filename = 'attendance_' + student_id + '.pdf'
    else:
        rows = query("""
            SELECT s.student_id, s.name, s.class_name,
                   COUNT(a.id) AS total_days,
                   SUM(CASE WHEN a.status='Present' THEN 1 ELSE 0 END) AS present_days
            FROM students s
            LEFT JOIN attendance a ON s.student_id = a.student_id
                AND TO_CHAR(a.date,'YYYY-MM') = %s
            GROUP BY s.student_id, s.name, s.class_name ORDER BY s.name
        """, (month,))
        title = 'Monthly Attendance Report - ' + month
        filename = 'attendance_' + month + '.pdf'

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=landscape(A4),
                            leftMargin=30, rightMargin=30, topMargin=40, bottomMargin=30)
    styles = getSampleStyleSheet()
    elements = []

    elements.append(Paragraph('SmartAttendance System', styles['Title']))
    elements.append(Paragraph(title, styles['Heading2']))
    elements.append(Spacer(1, 12))

    table_data = [['Student ID', 'Name', 'Class', 'Total', 'Present', 'Absent', 'Percentage', 'Status']]
    for r in rows:
        t = r['total_days'] or 0
        p = r['present_days'] or 0
        ab = t - p
        pct = round((p / t * 100) if t else 0, 1)
        status = 'Excellent' if pct >= 85 else ('Good' if pct >= 75 else 'Low')
        table_data.append([r['student_id'], r['name'], r['class_name'],
                           str(t), str(p), str(ab), str(pct) + '%', status])

    tbl = Table(table_data, repeatRows=1)
    tbl.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0f172a')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 11),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8fafc')]),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e2e8f0')),
        ('FONTSIZE', (0, 1), (-1, -1), 10),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]))
    elements.append(tbl)
    elements.append(Spacer(1, 20))
    elements.append(Paragraph('Generated on ' + datetime.now().strftime('%d %b %Y %H:%M'),
                               styles['Normal']))

    doc.build(elements)
    buffer.seek(0)

    response = make_response(buffer.read())
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = 'attachment; filename=' + filename
    return response


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
