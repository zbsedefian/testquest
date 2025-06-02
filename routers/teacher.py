# testquest/routers/teacher.py
from fastapi import APIRouter, Depends, HTTPException, Header
from pydantic import BaseModel
from sqlmodel import Session, select
from database import get_session
from dependencies import get_current_user
from models import TeacherStudent, User, TestResult, Test, StudentTestAssignment, Question
from typing import List, Optional


class TestResultOut(BaseModel):
    id: int
    student_id: int
    test_id: int
    score: int
    completed_at: str
    test_name: str

class StudentTestAssignmentCreate(BaseModel):
    test_id: int
    student_id: int

router = APIRouter(prefix="/teacher", tags=["teacher"])

@router.get("/students", response_model=List[User])
def get_assigned_students(current_user=Depends(get_current_user), session: Session = Depends(get_session)):
    if current_user.role == "student":
        raise HTTPException(status_code=403, detail="Not authorized")
    students = session.exec(
        select(User)
        .join(TeacherStudent, TeacherStudent.student_id == User.id)
        .where(TeacherStudent.teacher_id == current_user.id)
    ).all()
    return students

@router.get("/student/{student_id}/results", response_model=List[TestResultOut])
def get_student_results(
        student_id: int,
        current_user=Depends(get_current_user),
        session: Session = Depends(get_session),
):
    # Verify teacher is assigned to student
    assignment = session.exec(
        select(TeacherStudent)
        .where(TeacherStudent.teacher_id == current_user.id)
        .where(TeacherStudent.student_id == student_id)
    ).first()

    if not assignment:
        raise HTTPException(status_code=403, detail="Not authorized to view this student's data")

    results = session.exec(
        select(TestResult, Test.name)
        .join(Test, Test.id == TestResult.test_id)
        .where(TestResult.student_id == student_id)
    ).all()

    # Reshape for frontend
    return [
        {
            "id": r[0].id,
            "student_id": r[0].student_id,
            "test_id": r[0].test_id,
            "score": r[0].score,
            "completed_at": r[0].completed_at,
            "test_name": r[1]
        }
        for r in results
    ]

def teacher_required(user=Depends(get_current_user)):
    if user.role not in ["teacher", "admin"]:
        raise HTTPException(status_code=403, detail="Teachers or admin only")
    return user

@router.post("/assign-test", response_model=StudentTestAssignment)
def assign_test_to_student(data: StudentTestAssignmentCreate, session: Session = Depends(get_session), current_user=Depends(teacher_required)):
    # Verify teacher is assigned to student
    assignment = session.exec(
        select(TeacherStudent)
        .where(TeacherStudent.teacher_id == current_user.id)
        .where(TeacherStudent.student_id == data.student_id)
    ).first()

    if not assignment:
        raise HTTPException(status_code=403, detail="Not authorized to view this student's data")

    assignment = StudentTestAssignment(test_id=data.test_id, student_id=data.student_id)
    session.add(assignment)
    session.commit()
    session.refresh(assignment)
    return assignment

# Create a test
@router.post("/tests", response_model=Test)
def create_test(test: Test, session: Session = Depends(get_session), user: User = Depends(teacher_required)):
    test.created_by = user.id
    session.add(test)
    session.commit()
    session.refresh(test)
    return test

# Add questions to a test
@router.post("/tests/{test_id}/questions", response_model=Question)
def add_question(test_id: int, question: Question, session: Session = Depends(get_session), user: User = Depends(teacher_required)):
    test = session.get(Test, test_id)
    if not test:
        raise HTTPException(status_code=404, detail="Test not found")
    if test.created_by != user.id and user.role != "admin":
        raise HTTPException(status_code=403, detail="Not authorized")
    question.test_id = test_id
    session.add(question)
    session.commit()
    session.refresh(question)
    return question

# Assign a test to a student
@router.post("/assign-test")
def assign_test_to_student(student_id: int, test_id: int, session: Session = Depends(get_session), user: User = Depends(teacher_required)):
    # Verify teacher is assigned to student
    assignment = session.exec(
        select(TeacherStudent)
        .where(TeacherStudent.teacher_id == user.id)
        .where(TeacherStudent.student_id == student_id)
    ).first()

    if not assignment:
        raise HTTPException(status_code=403, detail="Not authorized to view this student's data")

    assignment = StudentTestAssignment(student_id=student_id, test_id=test_id)
    session.add(assignment)
    session.commit()
    return {"message": "Test assigned successfully"}


def get_current_teacher(
    x_user_id: Optional[int] = Header(None),
    session: Session = Depends(get_session),
) -> User:
    if x_user_id is None:
        raise HTTPException(status_code=401, detail="Missing x-user-id header")
    teacher = session.get(User, x_user_id)
    if not teacher or teacher.role != "teacher":
        raise HTTPException(status_code=403, detail="Unauthorized")
    return teacher


@router.get("/students", response_model=List[User])
def get_assigned_students(
    teacher: User = Depends(get_current_teacher),
    session: Session = Depends(get_session),
):
    # Query students assigned to this teacher via TeacherStudent table
    stmt = (
        select(User)
        .join(TeacherStudent, TeacherStudent.student_id == User.id)
        .where(TeacherStudent.teacher_id == teacher.id)
    )
    students = session.exec(stmt).all()
    return students


@router.get("/tests", response_model=List[Test])
def get_created_tests(
    teacher: User = Depends(get_current_teacher),
    session: Session = Depends(get_session),
):
    tests = session.exec(select(Test).where(Test.created_by == teacher.id)).all()
    return tests
