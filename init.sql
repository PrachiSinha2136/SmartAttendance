-- ─── Schema ─────────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS teachers (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS students (
    id SERIAL PRIMARY KEY,
    student_id VARCHAR(50) UNIQUE NOT NULL,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(100),
    class_name VARCHAR(50) NOT NULL DEFAULT 'General',
    fingerprint_id VARCHAR(255),
    face_encoding TEXT,
    registered_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS attendance (
    id SERIAL PRIMARY KEY,
    student_id VARCHAR(50) NOT NULL REFERENCES students(student_id) ON DELETE CASCADE,
    date DATE NOT NULL,
    status VARCHAR(10) NOT NULL DEFAULT 'Absent',
    method VARCHAR(20) NOT NULL DEFAULT 'manual',
    marked_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(student_id, date)
);

-- ─── Seed: Admin teacher ────────────────────────────────────────────────────
-- Password: admin123 (bcrypt via werkzeug)
INSERT INTO teachers (name, email, password_hash) VALUES
  ('Admin Teacher', 'admin@smart.edu',
   'scrypt:32768:8:1$coVP5X7MClPXxUbN$b869b8c9a53109c5c9e0fddeb208db94e850a3428bdb9ed60e29e2c1387579c73f67d14957b60450d104e0d21bc7400f998fad01ca5d59e7747b21a8f7c98a0f')
ON CONFLICT DO NOTHING;

-- ─── Seed: Students ─────────────────────────────────────────────────────────
INSERT INTO students (student_id, name, email, class_name, fingerprint_id) VALUES
  ('BC24001', 'Rahul Sharma',   'rahul@example.com',  'BCA Sem 1', 'FP_BC24001'),
  ('BC24002', 'Priya Singh',    'priya@example.com',  'BCA Sem 1', 'FP_BC24002'),
  ('BC24003', 'Aman Kumar',     'aman@example.com',   'BCA Sem 2', 'FP_BC24003'),
  ('BC24004', 'Neha Verma',     'neha@example.com',   'BCA Sem 2', 'FP_BC24004'),
  ('BC24005', 'Vikram Patel',   'vikram@example.com', 'BCA Sem 3', 'FP_BC24005')
ON CONFLICT DO NOTHING;

-- ─── Seed: Attendance – March 2026 ──────────────────────────────────────────
INSERT INTO attendance (student_id, date, status, method) VALUES
  ('BC24001','2026-03-02','Present','face'),
  ('BC24001','2026-03-03','Present','face'),
  ('BC24001','2026-03-04','Present','manual'),
  ('BC24001','2026-03-05','Absent','manual'),
  ('BC24001','2026-03-06','Present','face'),
  ('BC24001','2026-03-09','Present','fingerprint'),
  ('BC24001','2026-03-10','Present','face'),
  ('BC24001','2026-03-11','Absent','manual'),
  ('BC24001','2026-03-12','Present','face'),
  ('BC24001','2026-03-13','Present','face'),
  ('BC24002','2026-03-02','Present','face'),
  ('BC24002','2026-03-03','Absent','manual'),
  ('BC24002','2026-03-04','Present','fingerprint'),
  ('BC24002','2026-03-05','Present','face'),
  ('BC24002','2026-03-06','Absent','manual'),
  ('BC24002','2026-03-09','Present','face'),
  ('BC24002','2026-03-10','Present','face'),
  ('BC24002','2026-03-11','Present','fingerprint'),
  ('BC24002','2026-03-12','Absent','manual'),
  ('BC24002','2026-03-13','Present','face'),
  ('BC24003','2026-03-02','Absent','manual'),
  ('BC24003','2026-03-03','Absent','manual'),
  ('BC24003','2026-03-04','Present','face'),
  ('BC24003','2026-03-05','Absent','manual'),
  ('BC24003','2026-03-06','Present','fingerprint'),
  ('BC24003','2026-03-09','Absent','manual'),
  ('BC24003','2026-03-10','Present','face'),
  ('BC24003','2026-03-11','Absent','manual'),
  ('BC24003','2026-03-12','Present','face'),
  ('BC24003','2026-03-13','Absent','manual'),
  ('BC24004','2026-03-02','Present','fingerprint'),
  ('BC24004','2026-03-03','Present','face'),
  ('BC24004','2026-03-04','Present','face'),
  ('BC24004','2026-03-05','Present','fingerprint'),
  ('BC24004','2026-03-06','Present','face'),
  ('BC24004','2026-03-09','Present','face'),
  ('BC24004','2026-03-10','Present','fingerprint'),
  ('BC24004','2026-03-11','Present','face'),
  ('BC24004','2026-03-12','Present','face'),
  ('BC24004','2026-03-13','Present','fingerprint'),
  ('BC24005','2026-03-02','Present','face'),
  ('BC24005','2026-03-03','Present','face'),
  ('BC24005','2026-03-04','Absent','manual'),
  ('BC24005','2026-03-05','Present','fingerprint'),
  ('BC24005','2026-03-06','Present','face'),
  ('BC24005','2026-03-09','Absent','manual'),
  ('BC24005','2026-03-10','Present','face'),
  ('BC24005','2026-03-11','Present','face'),
  ('BC24005','2026-03-12','Present','fingerprint'),
  ('BC24005','2026-03-13','Present','face')
ON CONFLICT DO NOTHING;

-- ─── Seed: Attendance – April 2026 ──────────────────────────────────────────
INSERT INTO attendance (student_id, date, status, method) VALUES
  ('BC24001','2026-04-01','Present','face'),
  ('BC24001','2026-04-02','Present','face'),
  ('BC24001','2026-04-03','Absent','manual'),
  ('BC24001','2026-04-07','Present','fingerprint'),
  ('BC24001','2026-04-08','Present','face'),
  ('BC24002','2026-04-01','Present','face'),
  ('BC24002','2026-04-02','Absent','manual'),
  ('BC24002','2026-04-03','Present','face'),
  ('BC24002','2026-04-07','Present','fingerprint'),
  ('BC24002','2026-04-08','Absent','manual'),
  ('BC24003','2026-04-01','Absent','manual'),
  ('BC24003','2026-04-02','Present','face'),
  ('BC24003','2026-04-03','Absent','manual'),
  ('BC24003','2026-04-07','Absent','manual'),
  ('BC24003','2026-04-08','Present','fingerprint'),
  ('BC24004','2026-04-01','Present','fingerprint'),
  ('BC24004','2026-04-02','Present','face'),
  ('BC24004','2026-04-03','Present','face'),
  ('BC24004','2026-04-07','Present','fingerprint'),
  ('BC24004','2026-04-08','Present','face'),
  ('BC24005','2026-04-01','Present','face'),
  ('BC24005','2026-04-02','Present','fingerprint'),
  ('BC24005','2026-04-03','Present','face'),
  ('BC24005','2026-04-07','Absent','manual'),
  ('BC24005','2026-04-08','Present','face')
ON CONFLICT DO NOTHING;
