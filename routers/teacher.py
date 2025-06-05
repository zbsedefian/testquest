from fastapi import APIRouter, Depends, HTTPException, Header, Query
from pydantic import BaseModel
from sqlmodel import Session, select
from database import get_session
from dependencies import get_current_user
from models import User, TestResult, Test, StudentTestAssignment, Question, ClassroomStudentLink, ClassroomTeacherLink, \
    Classroom, ClassroomTestAssignment
from typing import List, Optional

class TestAssignmentRequest(BaseModel):
    student_id: int
    test_id: int

class TestResultWithName(BaseModel):
    id: int
    test_id: int
    student_id: int
    score: int
    completed_at: Optional[str]
    test_name: str

    class Config:
        orm_mode = True

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



class ClassroomWithStudents(BaseModel):
    classroom_id: int
    classroom_name: str
    students: List[User]


router = APIRouter(prefix="/teacher", tags=["teacher"])


def teacher_required(user=Depends(get_current_user)):
    print(user.role)
    if user.role not in ["teacher", "admin"]:
        raise HTTPException(status_code=403, detail="Teachers or admin only")
    return user


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


def get_current_teacher(
    x_user_id: Optional[int] = Header(None),
    session: Session = Depends(get_session),
) -> User:
    if x_user_id is None:
        raise HTTPException(status_code=401, detail="Missing x-user-id header")
    teacher = session.get(User, x_user_id)
    if not teacher or teacher.role != "teacher" or teacher.role != "admin":
        raise HTTPException(status_code=403, detail="Unauthorized")
    return teacher


@router.get("/students", response_model=List[ClassroomWithStudents])
def get_assigned_students(
    current_user=Depends(get_current_user),
    session: Session = Depends(get_session)
):
    if current_user.role != "teacher":
        raise HTTPException(status_code=403, detail="Only teachers can access this.")

    # Fetch all classrooms the teacher is assigned to
    classrooms = session.exec(
        select(Classroom)
        .join(ClassroomTeacherLink, ClassroomTeacherLink.classroom_id == Classroom.id)
        .where(ClassroomTeacherLink.teacher_id == current_user.id)
    ).all()

    result = []
    for cls in classrooms:
        student_links = session.exec(
            select(User)
            .join(ClassroomStudentLink, ClassroomStudentLink.student_id == User.id)
            .where(ClassroomStudentLink.classroom_id == cls.id)
        ).all()

        result.append({
            "classroom_id": cls.id,
            "classroom_name": cls.name,
            "students": student_links
        })

    return result



@router.get("/student/{student_id}/history", response_model=List[TestResultWithName])
def get_test_results(
    student_id: int,
    classroom_id: Optional[int] = None,
    current_user=Depends(get_current_user),
    session: Session = Depends(get_session),
):
    # if student_id and current_user.role not in {"teacher", "admin"}:
    #     raise HTTPException(status_code=403, detail="Not authorized")

    query = (
        select(TestResult, Test.name)
        .join(Test, TestResult.test_id == Test.id)
        .where(TestResult.student_id == student_id)
    )

    if classroom_id:
        query = query.join(ClassroomTestAssignment).where(
            ClassroomTestAssignment.classroom_id == classroom_id
        )

    results = session.exec(query).all()

    return [
        TestResultWithName(
            id=r.TestResult.id,
            test_id=r.TestResult.test_id,
            student_id=r.TestResult.student_id,
            score=r.TestResult.score,
            completed_at=r.TestResult.completed_at,
            test_name=r.name,
        )
        for r in results
    ]


