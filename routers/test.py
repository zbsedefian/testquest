from typing import List

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import delete
from sqlmodel import Session, select

from dependencies import get_current_user
from models import Classroom, ClassroomStudentLink, User, Test, ClassroomTeacherLink, \
    ClassroomTestAssignment, Question, TestResult
from database import get_session
from routers.teacher import TestCreate

router = APIRouter()


class TestClassroomAssignmentRequest(BaseModel):
    classroom_id: int
    test_id: int


def admin_required(user: User = Depends(get_current_user)):
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="Admins only")
    return user


@router.get("/tests/{test_id}", response_model=Test)
def get_test(test_id: int, session: Session = Depends(get_session)):
    test = session.get(Test, test_id)
    if not test:
        raise HTTPException(status_code=404, detail="Test not found")
    return test


@router.post("/tests")
def create_test(
    data: TestCreate,
    session: Session = Depends(get_session),
    user: User = Depends(get_current_user)
):
    test = Test(**data.dict(), created_by=user.id)
    session.add(test)
    session.commit()
    session.refresh(test)
    return test


@router.put("/tests/{test_id}", response_model=Test)
def update_test(
    test_id: int,
    data: TestCreate,  # reuse TestCreate schema if fields are same
    session: Session = Depends(get_session),
    user: User = Depends(get_current_user),
):
    test = session.get(Test, test_id)
    if not test:
        raise HTTPException(status_code=404, detail="Test not found")

    # Optional: enforce permission
    if test.created_by != user.id and user.role != "admin":
        raise HTTPException(status_code=403, detail="Not authorized to update this test")

    for field, value in data.dict().items():
        setattr(test, field, value)

    session.add(test)
    session.commit()
    session.refresh(test)
    return test


# Add questions to a test
@router.post("/tests/{test_id}/questions", response_model=Question)
def add_question(test_id: int, question: Question, session: Session = Depends(get_session), user: User = Depends(get_current_user)):
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


@router.get("/tests", response_model=List[Test])
def get_all_tests(
    user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    if user.role == "admin":
        return session.exec(select(Test)).all()

    if user.role == "teacher":
        # 1. Get classrooms this teacher is assigned to
        class_links = session.exec(
            select(ClassroomTeacherLink).where(ClassroomTeacherLink.teacher_id == user.id)
        ).all()
        classroom_ids = [link.classroom_id for link in class_links]

        # 2. Get all tests assigned to those classrooms
        class_test_links = session.exec(
            select(ClassroomTestAssignment).where(
                ClassroomTestAssignment.classroom_id.in_(classroom_ids)
            )
        ).all()
        assigned_test_ids = {link.test_id for link in class_test_links}

        # 3. Also include tests created by the teacher
        created_tests = session.exec(
            select(Test).where(Test.created_by == user.id)
        ).all()
        created_test_ids = {t.id for t in created_tests}

        # 4. Combine and fetch unique tests
        all_test_ids = assigned_test_ids.union(created_test_ids)
        if not all_test_ids:
            return []

        tests = session.exec(select(Test).where(Test.id.in_(all_test_ids))).all()
        return tests

    raise HTTPException(status_code=403, detail="Unauthorized role")


@router.post("/assign-test-to-classroom")
def assign_test_to_classroom(data: TestClassroomAssignmentRequest, session: Session = Depends(get_session), user: User = Depends(get_current_user)):
    # Prevent duplicates
    exists = session.exec(
        select(ClassroomTestAssignment)
        .where(ClassroomTestAssignment.classroom_id == data.classroom_id)
        .where(ClassroomTestAssignment.test_id == data.test_id)
    ).first()
    if not exists:
        session.add(ClassroomTestAssignment(classroom_id=data.classroom_id, test_id=data.test_id))
    session.commit()
    return {"message": "Assigned successfully"}


@router.get("/tests/{test_id}/assigned-classrooms")
def get_assigned_classrooms(test_id: int, session: Session = Depends(get_session), user: User = Depends(get_current_user)):
    links = session.exec(
        select(ClassroomTestAssignment).where(ClassroomTestAssignment.test_id == test_id)
    ).all()
    return {"classroom_ids": [link.classroom_id for link in links]}


@router.post("/unassign-test-from-classroom")
def unassign_test(data: TestClassroomAssignmentRequest, session: Session = Depends(get_session), user: User = Depends(get_current_user)):
    session.exec(
        delete(ClassroomTestAssignment)
        .where(ClassroomTestAssignment.test_id == data.test_id)
        .where(ClassroomTestAssignment.classroom_id == data.classroom_id)
    )
    session.commit()
    return {"message": "Unassigned successfully"}

class Score(BaseModel):
    score: int
    completed_at: str

class RankedResult(BaseModel):
    student_id: int
    username: str
    score: List[Score]


@router.get("/test/{test_id}/rankings")
def get_test_rankings(test_id: int, session: Session = Depends(get_session)):
    results = session.exec(
        select(TestResult, User.username)
        .join(User, TestResult.student_id == User.id)
        .where(TestResult.test_id == test_id)
    ).all()

    student_scores = {}
    for r, username in results:
        if r.student_id not in student_scores:
            student_scores[r.student_id] = {
                "student_id": r.student_id,
                "username": username,
                "attempts": [],
            }
        student_scores[r.student_id]["attempts"].append({
            "score": r.score,
            "completed_at": r.completed_at.isoformat()
        })

    return list(student_scores.values())
