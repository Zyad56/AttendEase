import os
from flask import (
    Flask, render_template, request, redirect, url_for, session,
    flash, make_response
)
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import date, datetime
from sqlalchemy import func, case, text
from io import StringIO
import csv

# Config
basedir = os.path.abspath(os.path.dirname(__file__))
app = Flask(__name__, instance_relative_config=True)
app.secret_key = 'replace-this-with-a-random-secret'
app.config['SQLALCHEMY_DATABASE_URI'] = (
    'sqlite:///' + os.path.join(basedir, 'instance', 'attendease.db')
)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Models
class User(db.Model):
    __tablename__ = 'Users'
    UserID    = db.Column(db.Integer, primary_key=True)
    Username  = db.Column(db.String(50), unique=True, nullable=False)
    Password  = db.Column(db.String(128), nullable=False)
    Name      = db.Column(db.String(100), nullable=False)
    Role_Type = db.Column(db.String(20), nullable=False)
    student   = db.relationship('Student',  back_populates='user',  uselist=False, cascade='all, delete-orphan')
    teacher   = db.relationship('Teacher',  back_populates='user',  uselist=False, cascade='all, delete-orphan')
    admin     = db.relationship('Admin',    back_populates='user',  uselist=False, cascade='all, delete-orphan')

class Student(db.Model):
    __tablename__ = 'Student'
    UserID         = db.Column(db.Integer, db.ForeignKey('Users.UserID'), primary_key=True)
    EnrollmentDate = db.Column(db.Date,    nullable=False)
    GraduationYear = db.Column(db.Integer)
    MajorField     = db.Column(db.String(100))
    user           = db.relationship('User', back_populates='student')
    enrollments    = db.relationship('Enrollments', backref='student', cascade='all, delete-orphan')

class Teacher(db.Model):
    __tablename__ = 'Teacher'
    UserID     = db.Column(db.Integer, db.ForeignKey('Users.UserID'), primary_key=True)
    HireDate   = db.Column(db.Date,    nullable=False)
    Department = db.Column(db.String(100))
    Rank       = db.Column(db.String(50))
    user       = db.relationship('User', back_populates='teacher')
    classes    = db.relationship('Classes', back_populates='teacher', cascade='all, delete-orphan')

class Admin(db.Model):
    __tablename__ = 'Admin'
    UserID           = db.Column(db.Integer, db.ForeignKey('Users.UserID'), primary_key=True)
    AdminLevel       = db.Column(db.Integer)
    OfficeLocation   = db.Column(db.String(100))
    Responsibilities = db.Column(db.Text)
    user             = db.relationship('User', back_populates='admin')

class Classes(db.Model):
    __tablename__ = 'Classes'
    ClassID     = db.Column(db.Integer, primary_key=True)
    ClassName   = db.Column(db.String(100), nullable=False)
    TeacherID   = db.Column(db.Integer, db.ForeignKey('Teacher.UserID'), nullable=False)
    Description = db.Column(db.Text)
    Schedule    = db.Column(db.String(200))
    teacher     = db.relationship('Teacher', back_populates='classes')
    enrollments = db.relationship('Enrollments', back_populates='class_', cascade='all, delete-orphan')

class Enrollments(db.Model):
    __tablename__ = 'Enrollments'
    EnrollmentID       = db.Column(db.Integer, primary_key=True)
    StudentID          = db.Column(db.Integer, db.ForeignKey('Student.UserID'), nullable=False)
    ClassID            = db.Column(db.Integer, db.ForeignKey('Classes.ClassID'), nullable=False)
    Status             = db.Column(db.String(20))
    EnrollDate         = db.Column(db.Date)
    class_             = db.relationship('Classes', back_populates='enrollments')
    attendance_records = db.relationship('Attendance', back_populates='enrollment', cascade='all, delete-orphan')

class Attendance(db.Model):
    __tablename__ = 'Attendance'
    EnrollmentID = db.Column(db.Integer, db.ForeignKey('Enrollments.EnrollmentID'), primary_key=True)
    Date         = db.Column(db.Date,    primary_key=True)
    Status       = db.Column(db.String(20))
    enrollment   = db.relationship('Enrollments', back_populates='attendance_records')

# Initialize DB, views & triggers
@app.cli.command('init-db')
def init_db():
    with app.app_context():
        db.create_all()
        # Views
        db.session.execute(text("""
        CREATE VIEW IF NOT EXISTS view_attendance_summary AS
        SELECT
          c.ClassName,
          u.Name AS StudentName,
          SUM(CASE WHEN a.Status='present' THEN 1 ELSE 0 END) AS PresentCount,
          COUNT(*) AS TotalCount,
          ROUND(CAST(SUM(CASE WHEN a.Status='present' THEN 1 ELSE 0 END) AS REAL)
            / COUNT(*) * 100.0, 2) AS AttendancePercentage
        FROM Attendance a
        JOIN Enrollments e ON a.EnrollmentID=e.EnrollmentID
        JOIN Classes c ON e.ClassID=c.ClassID
        JOIN Users u ON e.StudentID=u.UserID
        GROUP BY c.ClassName, u.Name;
        """))
        db.session.execute(text("""
        CREATE VIEW IF NOT EXISTS view_student_history AS
        SELECT
          e.StudentID,
          u.Name AS StudentName,
          c.ClassName,
          a.Date,
          a.Status
        FROM Attendance a
        JOIN Enrollments e ON a.EnrollmentID=e.EnrollmentID
        JOIN Classes c ON e.ClassID=c.ClassID
        JOIN Users u ON e.StudentID=u.UserID;
        """))
        # Triggers
        db.session.execute(text("""
        CREATE TRIGGER IF NOT EXISTS trg_validate_attendance_status
        BEFORE INSERT ON Attendance
        FOR EACH ROW
        BEGIN
          SELECT CASE WHEN NEW.Status NOT IN ('present','absent')
            THEN RAISE(ABORT, 'Invalid attendance status')
          END;
        END;
        """))
        db.session.execute(text("""
        CREATE TRIGGER IF NOT EXISTS trg_delete_attendance_on_enrollment_delete
        AFTER DELETE ON Enrollments
        FOR EACH ROW
        BEGIN
          DELETE FROM Attendance WHERE EnrollmentID = OLD.EnrollmentID;
        END;
        """))
        db.session.commit()
        print("Initialized DB with tables, views, and triggers.")

# === Application Routes ===

@app.route('/')
def select_role():
    return render_template('select_role.html')

@app.route('/login/<role>', methods=['GET','POST'])
def login_role(role):
    if role not in ['teacher','student','admin']:
        flash('Invalid role','danger')
        return redirect(url_for('select_role'))
    if request.method=='POST':
        user = User.query.filter_by(Username=request.form['username']).first()
        if user and check_password_hash(user.Password, request.form['password']) and user.Role_Type==role:
            session['user_id'] = user.UserID
            session['role']    = role
            return redirect(url_for('dashboard'))
        flash('Invalid credentials or wrong role','danger')
    return render_template('login.html', role=role)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('select_role'))

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('select_role'))
    role = session['role']
    if role=='teacher':
        teacher = Teacher.query.get(session['user_id'])
        dates = (db.session.query(Attendance.Date)
                 .join(Enrollments).join(Classes)
                 .filter(Classes.TeacherID==teacher.UserID)
                 .distinct().order_by(Attendance.Date.desc()).all())
        past_dates = [d[0] for d in dates]
        return render_template('teacher_dashboard.html',
                               classes=teacher.classes,
                               past_dates=past_dates)
    if role=='student':
        student = Student.query.get(session['user_id'])
        absences = []
        for enrol in student.enrollments:
            cnt = (db.session.query(func.count(Attendance.Status))
                   .filter(Attendance.EnrollmentID==enrol.EnrollmentID,
                           Attendance.Status=='absent')
                   .scalar() or 0)
            absences.append((enrol.class_.ClassName, cnt))
        return render_template('student_dashboard.html', absences=absences)
    if role=='admin':
        return render_template('admin_dashboard.html')
    return redirect(url_for('select_role'))

@app.route('/class/<int:class_id>/attendance', methods=['GET','POST'])
@app.route('/class/<int:class_id>/attendance/<string:att_date>', methods=['GET','POST'])
def take_attendance(class_id, att_date=None):
    if session.get('role')!='teacher':
        return redirect(url_for('select_role'))
    cls = Classes.query.get_or_404(class_id)
    if cls.TeacherID!=session['user_id']:
        flash('Not authorized','danger')
        return redirect(url_for('dashboard'))
    today = date.today() if not att_date else datetime.strptime(att_date,'%Y-%m-%d').date()
    existing = {r.EnrollmentID:r for r in Attendance.query.filter_by(Date=today)}
    if request.method=='POST':
        for enrol in cls.enrollments:
            status = request.form.get(f'status_{enrol.EnrollmentID}','absent')
            if enrol.EnrollmentID in existing:
                existing[enrol.EnrollmentID].Status = status
            else:
                db.session.add(Attendance(EnrollmentID=enrol.EnrollmentID, Date=today, Status=status))
        db.session.commit()
        flash('Attendance saved','success')
        return redirect(url_for('dashboard'))
    return render_template('take_attendance.html', cls=cls,
                           enrollments=cls.enrollments,
                           today=today, existing=existing)

# Admin CRUD
@app.route('/admin/users')
def admin_users():
    if session.get('role')!='admin':
        return redirect(url_for('select_role'))
    users = User.query.all()
    return render_template('admin_users.html', users=users)

@app.route('/admin/users/create', methods=['GET','POST'])
def admin_create_user():
    if session.get('role')!='admin':
        return redirect(url_for('select_role'))
    all_classes = Classes.query.all()
    if request.method=='POST':
        role = request.form['role']
        pw_hash = generate_password_hash(request.form['password'])
        user = User(Username=request.form['username'],
                    Password=pw_hash,
                    Name=request.form['name'],
                    Role_Type=role)
        db.session.add(user)
        db.session.commit()
        if role=='student':
            stu = Student(UserID=user.UserID,
                          EnrollmentDate=date.today(),
                          GraduationYear=None,
                          MajorField=None)
            db.session.add(stu)
            db.session.commit()
            chosen = int(request.form['class_id'])
            enrol = Enrollments(StudentID=user.UserID,
                                ClassID=chosen,
                                Status='active',
                                EnrollDate=date.today())
            db.session.add(enrol)
            db.session.commit()
        flash('User created successfully!','success')
        return redirect(url_for('admin_users'))
    return render_template('admin_create_user.html', classes=all_classes)

@app.route('/admin/users/edit/<int:user_id>', methods=['GET','POST'])
def admin_edit_user(user_id):
    if session.get('role')!='admin':
        return redirect(url_for('select_role'))
    user = User.query.get_or_404(user_id)
    if request.method=='POST':
        user.Username   = request.form['username']
        user.Name       = request.form['name']
        user.Role_Type  = request.form['role']
        db.session.commit()
        flash('User updated successfully!','success')
        return redirect(url_for('admin_users'))
    return render_template('admin_edit_user.html', user=user)

@app.route('/admin/users/delete/<int:user_id>', methods=['POST'])
def admin_delete_user(user_id):
    if session.get('role')!='admin':
        return redirect(url_for('select_role'))
    user = User.query.get_or_404(user_id)
    db.session.delete(user)
    db.session.commit()
    flash(f'User {user.Username} deleted.','info')
    return redirect(url_for('admin_users'))

@app.route('/reports/summary')
def report_summary():
    if session.get('role') not in ['teacher','admin']:
        return redirect(url_for('select_role'))

    # pass class list for dropdown
    classes = Classes.query.order_by(Classes.ClassName).all()

    class_filter   = request.args.get('class_id',    type=int)
    student_filter = request.args.get('student_name', '')

    qry = (
        db.session.query(
            Classes.ClassName,
            User.Name.label('StudentName'),
            func.sum(case((Attendance.Status=='present',1), else_=0)).label('PresentCount'),
            func.count(Attendance.Status).label('TotalCount'),
            (func.sum(case((Attendance.Status=='present',1),else_=0))
             / func.count(Attendance.Status)*100).label('AttendancePct')
        )
        .join(Enrollments, Attendance.EnrollmentID==Enrollments.EnrollmentID)
        .join(Classes,    Enrollments.ClassID==Classes.ClassID)
        .join(User,       Enrollments.StudentID==User.UserID)
    )

    if class_filter:
        qry = qry.filter(Classes.ClassID==class_filter)
    if student_filter:
        qry = qry.filter(User.Name.ilike(f"%{student_filter}%"))

    results = qry.group_by(Classes.ClassName, User.Name).all()

    if request.args.get('export') == 'csv':
        si = StringIO()
        cw = csv.writer(si)
        cw.writerow(['ClassName','StudentName','PresentCount','TotalCount','AttendancePct'])
        for row in results:
            cw.writerow(row)
        output = make_response(si.getvalue())
        output.headers['Content-Disposition'] = 'attachment; filename=attendance_summary.csv'
        output.headers['Content-Type'] = 'text/csv'
        return output

    return render_template(
        'report_summary.html',
        classes=classes,
        results=results,
        selected_class=class_filter,
        student_filter=student_filter
    )

if __name__ == '__main__':
    app.run(debug=True)
