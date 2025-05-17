from app import app, db
from sqlalchemy import text

if __name__ == "__main__":
    with app.app_context():
        db.create_all()

        # Views
        db.session.execute(text("""
        CREATE VIEW IF NOT EXISTS view_attendance_summary AS
        SELECT
          c.ClassName,
          u.Name       AS StudentName,
          SUM(CASE WHEN a.Status = 'present' THEN 1 ELSE 0 END) AS PresentCount,
          COUNT(*)                                         AS TotalCount,
          ROUND(
            CAST(SUM(CASE WHEN a.Status = 'present' THEN 1 ELSE 0 END) AS REAL)
            / COUNT(*) * 100.0,
            2
          ) AS AttendancePercentage
        FROM Attendance a
        JOIN Enrollments e ON a.EnrollmentID = e.EnrollmentID
        JOIN Classes     c ON e.ClassID      = c.ClassID
        JOIN Users       u ON e.StudentID    = u.UserID
        GROUP BY c.ClassName, u.Name;
        """))

        db.session.execute(text("""
        CREATE VIEW IF NOT EXISTS view_student_history AS
        SELECT
          e.StudentID,
          u.Name       AS StudentName,
          c.ClassName,
          a.Date,
          a.Status
        FROM Attendance a
        JOIN Enrollments e ON a.EnrollmentID = e.EnrollmentID
        JOIN Classes     c ON e.ClassID      = c.ClassID
        JOIN Users       u ON e.StudentID    = u.UserID;
        """))

        # Triggers
        db.session.execute(text("""
        CREATE TRIGGER IF NOT EXISTS trg_validate_attendance_status
        BEFORE INSERT ON Attendance
        FOR EACH ROW
        BEGIN
          SELECT CASE
            WHEN NEW.Status NOT IN ('present','absent')
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
        print("✅ Database tables, views & triggers created!")
