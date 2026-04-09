# SmartAttendance

A full-featured, Docker-ready attendance management system with biometric support (Face, Fingerprint demo, Manual), teacher dashboard, per-student reports, and CSV/PDF exports — backed by Flask + PostgreSQL.

---

## Quick Start

```bash
docker compose up --build
```

Open **http://localhost:5000**

**Default login:** `admin@smart.edu` / `admin123`

---

## Features

| Feature | Description |
|---|---|
| **Login / Auth** | Session-based teacher login |
| **Dashboard** | Stats cards, weekly bar+line chart, per-student attendance table |
| **Register Student** | Webcam face capture (demo), simulated fingerprint, form fields |
| **Mark Attendance** | 3 modes: Face (webcam), Fingerprint (ID match), Manual dropdown |
| **Reports** | Filter by month/class/student, 6-month trend chart |
| **Per-Student Detail** | Doughnut chart, monthly trend, full history table |
| **Download CSV** | Monthly or per-student CSV export |
| **Download PDF** | Styled PDF via ReportLab |
| **PostgreSQL** | Full schema with seed data (5 students, 2 months of records) |
| **Docker** | `docker-compose.yml` with health checks |

---

## Services

| Service | Port | Description |
|---|---|---|
| `app` | 5000 | Flask application |
| `db` | 5432 | PostgreSQL 15 |

---

## Environment Variables

| Variable | Default | Description |
|---|---|---|
| `DATABASE_URL` | postgresql://admin:smartpass123@db:5432/attendance_system | PostgreSQL URL |
| `SECRET_KEY` | dev-key | Flask session secret |

Copy `.env.example` to `.env` and edit for production.

---

## Manual Run (without Docker)

```bash
pip install -r requirements.txt
# Set up a local PostgreSQL DB and run init.sql
DATABASE_URL=postgresql://user:pass@localhost/attendance_system python app.py
```

---

## Attendance Modes

- **Face Recognition** – Webcam captures image (stored as base64); demo always matches — integrate real face comparison (e.g. `face_recognition` lib) as needed.
- **Fingerprint** – A unique ID (`FP_<student_id>`) is assigned at registration; at attendance time, typing/pasting the same ID matches. Connect real scanner hardware to replace the simulation.
- **Manual** – Dropdown of students, date picker, Present/Absent/Late selector.
