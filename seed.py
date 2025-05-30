# testquest/seed.py
from sqlmodel import Session
from database import engine
from models import User, TeacherStudent, Test, Question, StudentTestAssignment

print("Seeding database...")

with Session(engine) as session:
    # Users
    admin = User(username="admin", password="password", role="admin")
    teacher = User(username="teacher", password="password", role="teacher")
    student = User(username="student1", password="password", role="student")
    student2 = User(username="student2", password="password", role="student")
    session.add_all([admin, teacher, student, student2])
    session.commit()

    # Link teacher to student
    session.add(TeacherStudent(teacher_id=teacher.id, student_id=student.id))
    session.add(TeacherStudent(teacher_id=teacher.id, student_id=student2.id))

    # Test and Questions
    test = Test(name="Practice SHSAT 1", created_by=teacher.id)
    session.add(test)
    session.commit()

    session.add(StudentTestAssignment(student_id=student.id, test_id=test.id))
    session.add(StudentTestAssignment(student_id=student2.id, test_id=test.id))
    session.commit()

    q1 = Question(
        test_id=test.id,
        question_text="What is 2 + 2?",
        choices='{ "A": "3", "B": "4", "C": "5", "D": "6" }',
        correct_choice="B",
        explanation="Algebra"
    )
    q2 = Question(
        test_id=test.id,
        question_text="Which is a prime number?",
        choices='{ "A": "4", "B": "6", "C": "7", "D": "9" }',
        correct_choice="C",
        explanation="Number Theory"
    )

    session.add_all([q1, q2])
    session.commit()

print("✅ Done seeding!")
