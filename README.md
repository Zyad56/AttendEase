# AttendEase

**AttendEase** is a web application built with Flask and SQLite for managing and tracking student attendance. It supports teacher, student, and admin roles, with features for taking attendance, viewing absence counts, managing users, and generating attendance reports.

---

## 📋 Prerequisites

* Python 3.9+
* Git
* (Optional) Virtual environment tool, e.g. `venv`

---

## 🛠 Installation

1. **Clone the repository**

   ```bash
   git clone https://github.com/Zyad56/AttendEase.git
   cd AttendEase
   ```

2. **Set up a virtual environment**

   ```bash
   python -m venv venv
   .\venv\Scripts\Activate    # Windows PowerShell
   # source venv/bin/activate   # macOS/Linux
   ```

3. **Install dependencies**

   ```bash
   pip install -r requirements.txt
   ```

---

## ⚙ Database Initialization & Seeding

1. **Create tables, views & triggers**

   ```bash
   flask init-db
   # or: python -m flask init-db
   ```
2. **Seed sample data** (admin, professors, classes, students, enrollments)

   ```bash
   python seed_data.py
   ```

---

## 🚀 Running the App

```bash
python app.py
```

Then open your browser at `http://127.0.0.1:5000/`.

---

## 🔑 Default Test Credentials

### Admin

```
ID: 00001
Password: adminpass
```

### Professors (5)

```
10001 / password
10002 / password
10003 / password
10004 / password
10005 / password
```

### Students (50)

```
11001 / password
11002 / password
...   / password
11050 / password
```

---

## 🎓 Usage Guide

1. **Select your role** on the homepage.
2. **Log in** with your ID and password.
3. **Teacher**:

   * Dashboard lists your courses and dates.
   * Click **Today** (or past dates) to take attendance.
4. **Student**:

   * Dashboard shows enrolled courses and days absent.
5. **Admin**:

   * Manage users (create/edit/delete).
   * View **Reports**: filter by course or student, export CSV.

---

## 📁 Project Structure

```
AttendEase/
├─ app.py
├─ init_db.py
├─ seed_data.py
├─ requirements.txt
├─ instance/attendease.db
├─ static/
│  └─ css/style.css
└─ templates/
   ├─ layout.html
   ├─ select_role.html
   ├─ login.html
   ├─ teacher_dashboard.html
   ├─ student_dashboard.html
   ├─ take_attendance.html
   ├─ report_summary.html
   ├─ admin_dashboard.html
   ├─ admin_users.html
   ├─ admin_create_user.html
   └─ admin_edit_user.html
```

---

## ⚖ License

This project is released under the **MIT License**. Feel free to use, modify, and distribute for educational purposes.

```text
MIT License

Copyright (c) 2025 Your Name

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software... [rest of MIT license text]
```

---

**Tip:** After adding this file, commit and push:

```bash
git add README.md
git commit -m "Add README with setup & usage"
git push
```
