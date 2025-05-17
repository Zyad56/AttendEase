# seed_data.py
from app import app, db, User, Admin, Teacher, Student, Classes, Enrollments
from werkzeug.security import generate_password_hash
from datetime import date
import random

# Name pools
prof_first = ['Alice','Bob','Carol','David','Eva']
prof_last  = ['Smith','Johnson','Williams','Brown','Jones']
stud_first = ['Liam','Emma','Noah','Olivia','William','Ava','James','Isabella','Logan','Sophia']
stud_last  = ['Miller','Davis','Garcia','Rodriguez','Wilson','Martinez','Anderson','Taylor','Thomas','Hernandez']

# Course code prefixes
course_codes = ['CSC','FIN','MAT','PHY','HIS']

with app.app_context():
    # 1) Rebuild schema
    db.drop_all()
    db.create_all()

    # 2) Seed Admin
    admin_user = User(
        Username='00001',
        Password=generate_password_hash('adminpass'),
        Name='Site Administrator',
        Role_Type='admin'
    )
    db.session.add(admin_user)
    db.session.commit()
    db.session.add(
        Admin(
            UserID=admin_user.UserID,
            AdminLevel=1,
            OfficeLocation='HQ Office',
            Responsibilities='Full system administration'
        )
    )
    db.session.commit()

    # 3) Seed Professors (5) and Classes (20)
    prof_users = []
    for i in range(5):
        # Unique 5-digit ID
        prof_id = f"{10000 + i + 1:05d}"
        full_name = f"{prof_first[i]} {prof_last[i]}"
        # Create User+Teacher
        pu = User(
            Username=prof_id,
            Password=generate_password_hash('password'),
            Name=full_name,
            Role_Type='teacher'
        )
        db.session.add(pu)
        db.session.commit()
        prof_users.append(pu)

        t = Teacher(UserID=pu.UserID, HireDate=date(2020,1,i+1),
                    Department=f"Department {i+1}", Rank='Professor')
        db.session.add(t)
        db.session.commit()

    # Now create 20 classes, assigning them evenly to the 5 profs
    classes = []
    for idx in range(20):
        code = course_codes[idx % len(course_codes)]
        num  = 1001 + idx
        cls = Classes(
            ClassName=f"{code} {num}",
            TeacherID=prof_users[idx % len(prof_users)].UserID,
            Description=f"Description for {code} {num}",
            Schedule='Mon & Wed 10:00-11:30'
        )
        db.session.add(cls)
        db.session.commit()
        classes.append(cls)

    # 4) Seed 50 Students
    student_users = []
    for j in range(50):
        stud_id = f"{11000 + j + 1:05d}"
        full_name = f"{random.choice(stud_first)} {random.choice(stud_last)}"
        su = User(
            Username=stud_id,
            Password=generate_password_hash('password'),
            Name=full_name,
            Role_Type='student'
        )
        db.session.add(su)
        db.session.commit()
        student_users.append(su)

        st = Student(UserID=su.UserID, EnrollmentDate=date.today(),
                     GraduationYear=2027, MajorField='General Studies')
        db.session.add(st)
        db.session.commit()

    # 5) Enroll each student in 5 *distinct* random classes
    for su in student_users:
        chosen = random.sample(classes, 5)
        for cls in chosen:
            e = Enrollments(
                StudentID=su.UserID,
                ClassID=cls.ClassID,
                Status='active',
                EnrollDate=date.today()
            )
            db.session.add(e)
    db.session.commit()

    print("✅ Seed complete: 1 admin, 5 profs, 20 classes, 50 students, each student in 5 classes.")
