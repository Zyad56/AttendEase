# tests/test_app.py
import os, sys
# ensure project root is on Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pytest
from app import app, db, User, Teacher, Student, Classes, Enrollments, Attendance
from werkzeug.security import generate_password_hash
from datetime import date

@pytest.fixture
def client():
    # configure Flask for testing
    app.config['TESTING'] = True
    with app.test_client() as client:
        with app.app_context():
            db.drop_all()
            db.create_all()
            # seed minimal data: one teacher
            user = User(
                Username='t1',
                Password=generate_password_hash('pw'),
                Name='T Tester',
                Role_Type='teacher'
            )
            db.session.add(user)
            db.session.commit()
            teacher = Teacher(UserID=user.UserID, HireDate=date.today())
            db.session.add(teacher)
            db.session.commit()
        yield client

def test_login_page_renders(client):
    rv = client.get('/login')
    assert b'<h2>Login</h2>' in rv.data

def test_invalid_login_shows_error(client):
    rv = client.post('/login',
                     data={'username':'wrong','password':'wrong'},
                     follow_redirects=True)
    assert b'Invalid username or password' in rv.data

def test_teacher_login_and_dashboard(client):
    # login with seeded user
    rv = client.post('/login',
                     data={'username':'t1','password':'pw'},
                     follow_redirects=True)
    # should land on the dashboard showing "Your Classes"
    assert b'Your Classes' in rv.data

def test_take_attendance_requires_login(client):
    # unauthenticated access should redirect to login
    rv = client.get('/class/1/attendance', follow_redirects=True)
    assert b'<h2>Login</h2>' in rv.data
