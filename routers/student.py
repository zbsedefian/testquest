# testquest/routers/student.py
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from dependencies import get_current_user
from database import get_session
from models import Test, Question, StudentAnswer, TestResult, User, StudentTestAssignment
from pydantic import BaseModel
from typing import List

router = APIRouter(prefix="/student", tags=["student"])

class AnswerRequest(BaseModel):
    question_id: int
    selected_choice: str

class TestSubmitRequest(BaseModel):
    student_id: int
    test_id: int
    answers: List[AnswerRequest]

@router.get("/tests", response_model=List[Test])
def get_assigned_tests(
        current_user=Depends(get_current_user),
        session: Session = Depends(get_session),
):
    if current_user.role != "student" and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Only students or admins allowed")
    print("Current user:", current_user)
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
    return session.exec(select(Question).where(Question.test_id == test_id)).all()

@router.post("/submit")
def submit_test(data: TestSubmitRequest, session: Session = Depends(get_session)):
    score = 0
    for ans in data.answers:
        question = session.get(Question, ans.question_id)
        is_correct = question.correct_choice == ans.selected_choice
        if is_correct:
            score += 1
        session.add(StudentAnswer(
            student_id=data.student_id,
            question_id=ans.question_id,
            selected_choice=ans.selected_choice,
            is_correct=is_correct
        ))

    session.add(TestResult(
        student_id=data.student_id,
        test_id=data.test_id,
        score=score
    ))
    session.commit()
    return {"score": score}
