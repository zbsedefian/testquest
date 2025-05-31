# testquest/routers/admin.py
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from database import get_session
from models import User, TeacherStudent, TestTeacherAssignment, Test
from typing import List
from dependencies import get_current_user

from pydantic import BaseModel

class UserCreate(BaseModel):
    username: str
    password: str
    role: str  # "teacher" or "student"

class TeacherStudentCreate(BaseModel):
    teacher_id: int
    student_id: int

class TestTeacherAssignmentCreate(BaseModel):
    test_id: int
    teacher_id: int


router = APIRouter(prefix="/admin", tags=["admin"])

# Utility: Only allow admin users to access these routes
def admin_required(user: User = Depends(get_current_user)):
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="Admins only")
    return user


@router.get("/tests", response_model=List[Test])
def list_tests(
    current_user = Depends(admin_required),
    session: Session = Depends(get_session)
):
    tests = session.exec(select(Test)).all()
    return tests


@router.get("/users", response_model=List[User])
def list_users(
    current_user: User = Depends(admin_required),  # Ensure user is admin
    session: Session = Depends(get_session)       # DB session for querying
):
    users = session.exec(select(User)).all()
    return users


@router.post("/create-user", response_model=User)
def create_user(data: UserCreate, session: Session = Depends(get_session), current_user: User = Depends(admin_required)):
    user = User(username=data.username, password=data.password, role=data.role)
    session.add(user)
    session.commit()
    session.refresh(user)
    return user

@router.post("/assign-student-to-teacher", response_model=TeacherStudent)
def assign_student_to_teacher(data: TeacherStudentCreate, session: Session = Depends(get_session), current_user: User = Depends(admin_required)):
    assignment = TeacherStudent(teacher_id=data.teacher_id, student_id=data.student_id)
    session.add(assignment)
    session.commit()
    session.refresh(assignment)
    return assignment

@router.post("/assign-test-to-teacher", response_model=TestTeacherAssignment)
def assign_test_to_teacher(data: TestTeacherAssignmentCreate, session: Session = Depends(get_session), current_user: User = Depends(admin_required)):
    assignment = TestTeacherAssignment(test_id=data.test_id, teacher_id=data.teacher_id)
    session.add(assignment)
    session.commit()
    session.refresh(assignment)
    return assignment