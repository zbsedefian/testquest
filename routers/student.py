# testquest/routers/student.py
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import delete
from sqlmodel import Session, select
from dependencies import get_current_user
from database import get_session
from models import Test, Question, StudentAnswer, TestResult, User, StudentTestAssignment, ClassroomStudentLink, \
    Classroom
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
    if current_user.role != "student" and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Only students or admins allowed")
    assignments = session.exec(
        select(StudentTestAssignment).where(StudentTestAssignment.student_id == current_user.id)
    ).all()

    test_ids = [assignment.test_id for assignment in assignments]
    if not test_ids:
        return []  # no tests assigned

    tests = session.exec(select(Test).where(Test.id.in_(test_ids))).all()
    return tests

@router.get("/test/{test_id}", response_model=List[Question])
def get_test_questions(test_id: int, session: Session = Depends(get_session)):
    questions = session.exec(
        select(Question).where(Question.test_id == test_id).order_by(Question.order)
    ).all()
    return questions

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
    # prevent re-submission
    existing = session.exec(
        select(TestResult).where(
            TestResult.student_id == current_user.id,
            TestResult.test_id == data.test_id
        )
    ).first()
    # if existing:
    #     raise HTTPException(status_code=400, detail="Test already submitted.")

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

    session.add(TestResult(
        student_id=current_user.id,
        test_id=data.test_id,
        score=score,
        completed_at=datetime.now()
    ))
    session.commit()
    return {"score": score}


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

