from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import delete
from sqlmodel import Session, select
from dependencies import get_current_user
from database import get_session
from models import Test, Question, StudentAnswer, TestResult, User, ClassroomStudentLink, \
    Classroom, ClassroomTestAssignment
from pydantic import BaseModel
from typing import List, Optional

router = APIRouter(prefix="/student", tags=["student"])

class TestResultWithName(BaseModel):
    id: int
    test_id: int
    student_id: int
    score: int
    completed_at: Optional[str]
    test_name: str

    class Config:
        orm_mode = True

class AnswerRequest(BaseModel):
    question_id: int
    selected_choice: str

class TestSubmitRequest(BaseModel):
    test_id: int
    answers: List[AnswerRequest]


@router.get("/tests", response_model=List[Test])
def get_assigned_tests(
    current_user=Depends(get_current_user),
    session: Session = Depends(get_session),
):
    if current_user.role not in {"student", "admin"}:
        raise HTTPException(status_code=403, detail="Only students or admins allowed")

    # Get classroom IDs for this student
    classroom_links = session.exec(
        select(ClassroomStudentLink.classroom_id).where(ClassroomStudentLink.student_id == current_user.id)
    ).all()
    classroom_ids = classroom_links  # Already a list of ints

    # Get test IDs assigned to those classrooms
    if classroom_ids:
        classroom_assignments = session.exec(
            select(ClassroomTestAssignment.test_id).where(ClassroomTestAssignment.classroom_id.in_(classroom_ids))
        ).all()
        classroom_test_ids = set(classroom_assignments)
    else:
        classroom_test_ids = set()

    if not classroom_test_ids:
        return []

    tests = session.exec(select(Test).where(Test.id.in_(classroom_test_ids))).all()
    return tests


@router.get("/test/{test_id}/meta")
def get_test_meta(test_id: int, session: Session = Depends(get_session)):
    test = session.get(Test, test_id)
    if not test:
        raise HTTPException(status_code=404, detail="Test not found")
    return test


@router.get("/test/{test_id}")
def get_test_with_questions(test_id: int, session: Session = Depends(get_session)):
    test = session.get(Test, test_id)
    if not test:
        raise HTTPException(status_code=404, detail="Test not found")

    questions = session.exec(
        select(Question).where(Question.test_id == test_id).order_by(Question.order)
    ).all()

    return {
        "id": test.id,
        "name": test.name,
        "duration_minutes": test.duration_minutes,
        "is_timed": test.is_timed,
        "questions": questions,
    }

@router.get("/test-results", response_model=List[TestResultWithName])
def get_test_results(
    current_user=Depends(get_current_user),
    session: Session = Depends(get_session),
):
    results = session.exec(
        select(TestResult, Test.name)
        .join(Test, TestResult.test_id == Test.id)
        .where(TestResult.student_id == current_user.id)
        .order_by(TestResult.id)
    ).all()

    return [
        TestResultWithName(
            id=result.TestResult.id,
            test_id=result.TestResult.test_id,
            student_id=result.TestResult.student_id,
            score=result.TestResult.score,
            completed_at=result.TestResult.completed_at,
            test_name=result.name,
        )
        for result in results
    ]

@router.post("/submit")
def submit_test(
    data: TestSubmitRequest,
    session: Session = Depends(get_session),
    current_user=Depends(get_current_user)
):
    test = session.get(Test, data.test_id)
    if not test:
        raise HTTPException(status_code=404, detail="Test not found.")

    existing_attempts = session.exec(
        select(TestResult).where(
            TestResult.student_id == current_user.id,
            TestResult.test_id == data.test_id
        )
    ).all()

    attempt_number = len(existing_attempts) + 1

    # Grade the test
    score = 0
    for ans in data.answers:
        question = session.get(Question, ans.question_id)
        if not question:
            raise HTTPException(status_code=400, detail=f"Question ID {ans.question_id} not found.")
        is_correct = question.correct_choice == ans.selected_choice
        if is_correct:
            score += 1
        session.add(StudentAnswer(
            student_id=current_user.id,
            question_id=ans.question_id,
            selected_choice=ans.selected_choice,
            is_correct=is_correct
        ))

    # Final score as percentage
    if not data.answers:
        percentage_score = 0
    else:
        percentage_score = round((score / len(data.answers)) * 100)

    # Save test result
    session.add(TestResult(
        student_id=current_user.id,
        test_id=data.test_id,
        score=round(percentage_score, 2),
        completed_at=datetime.utcnow(),
        attempt_number=attempt_number
    ))

    session.commit()
    return {"score": round(percentage_score, 2), "attempt": len(existing_attempts) + 1}



@router.post("/{student_id}/classrooms")
def set_student_classrooms(
    student_id: int,
    payload: List[int],  # list of classroom IDs
    session: Session = Depends(get_session)
):
    # Remove existing links
    session.exec(
        delete(ClassroomStudentLink).where(ClassroomStudentLink.student_id == student_id)
    )
    # Add new links
    for cls_id in payload:
        session.add(ClassroomStudentLink(classroom_id=cls_id, student_id=student_id))
    session.commit()
    return {"message": "Updated student classrooms"}


@router.get("/{student_id}/classrooms")
def get_student_classrooms(student_id: int, session: Session = Depends(get_session)):
    statement = (
        select(Classroom)
        .join(ClassroomStudentLink)
        .where(ClassroomStudentLink.student_id == student_id)
    )
    return session.exec(statement).all()


@router.get("/tests/attempts/{test_id}")
def get_attempt_count(test_id: int, session: Session = Depends(get_session), current_user=Depends(get_current_user)):
    attempts = session.exec(
        select(TestResult).where(
            TestResult.student_id == current_user.id,
            TestResult.test_id == test_id
        )
    ).all()
    return {"attempt_count": len(attempts)}
