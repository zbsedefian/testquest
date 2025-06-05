from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Path, Body
from pydantic import BaseModel
from sqlalchemy import func
from sqlmodel import Session, select

from database import get_session
from dependencies import get_current_user
from models import User, TeacherStudent, TestTeacherAssignment, Test, ClassroomStudentLink, ClassroomTeacherLink, \
    Classroom


class UserCreate(BaseModel):
    username: str
    password: str
    role: str  # "teacher" or "student"

class UserUpdate(BaseModel):
    username: Optional[str] = None
    password: Optional[str] = None
    role: Optional[str] = None  # "teacher" or "student" or "admin"

class TeacherStudentCreate(BaseModel):
    teacher_id: int
    student_id: int

class TestTeacherAssignmentCreate(BaseModel):
    test_id: int
    teacher_id: int

class UserOut(BaseModel):
    id: int
    username: str
    role: str

    class Config:
        orm_mode = True

class PaginatedUsers(BaseModel):
    users: List[UserOut]
    total: int
    page: int
    total_pages: int
    per_page: int

class RelatedUsersOut(BaseModel):
    students: Optional[List[UserOut]] = None
    teacher: Optional[UserOut] = None

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


@router.get("/users/all", response_model=List[User])
def get_all_users(
    session: Session = Depends(get_session),
    user: User = Depends(admin_required),
):
    return session.exec(select(User)).all()


@router.get("/users", response_model=PaginatedUsers)
def get_users(
    page: int = Query(1, ge=1),
    per_page: int = Query(10, le=100),
    role: Optional[str] = None,
    search: Optional[str] = None,
    session: Session = Depends(get_session),
    user: User = Depends(get_current_user),
):
    if user.role == "teacher" and role != "student":
        raise HTTPException(status_code=403, detail="Admins only")

    if user.role == "student":
        raise HTTPException(status_code=403, detail="Admins only")

    filters = []
    if role:
        filters.append(User.role == role)
    if search:
        filters.append(User.username.ilike(f"%{search}%"))

    total = session.exec(select(func.count()).select_from(User).where(*filters)).one()

    statement = select(User).where(*filters).offset((page - 1) * per_page).limit(per_page)
    users = session.exec(statement).all()

    total_pages = max(1, (total + per_page - 1) // per_page)

    return {
        "users": users,
        "total": total,
        "page": page,
        "per_page": per_page,
        "total_pages": total_pages,
    }


@router.post("/user", response_model=User)
def create_user(
    data: UserCreate,
    session: Session = Depends(get_session),
    user: User = Depends(get_current_user)
):
    if user.role == "teacher" and data.role != "student":
        raise HTTPException(status_code=403, detail="Admins only")

    if user.role == "student":
        raise HTTPException(status_code=403, detail="Admins only")

    user = User(username=data.username, password=data.password, role=data.role)
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


@router.put("/user/{user_id}", response_model=User)
def edit_user(
    user_id: int = Path(..., ge=1),
    data: UserUpdate = Body(...),
    session: Session = Depends(get_session),
    current_user: User = Depends(admin_required)
):
    user = session.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if data.username is not None:
        user.username = data.username
    if data.password is not None:
        user.password = data.password
    if data.role is not None:
        user.role = data.role

    session.add(user)
    session.commit()
    session.refresh(user)
    return user


@router.delete("/user/{user_id}", status_code=204)
def delete_user(
    user_id: int = Path(..., ge=1),
    session: Session = Depends(get_session),
    current_user: User = Depends(admin_required)
):
    user = session.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    session.delete(user)
    session.commit()
    return None  # 204 No Content returns empty response


@router.post("/assign-student-to-teacher", response_model=TeacherStudent)
def assign_student_to_teacher(
    data: TeacherStudentCreate,
    session: Session = Depends(get_session),
    current_user: User = Depends(admin_required)
):
    assignment = TeacherStudent(teacher_id=data.teacher_id, student_id=data.student_id)
    session.add(assignment)
    session.commit()
    session.refresh(assignment)
    return assignment


@router.post("/assign-test-to-teacher", response_model=TestTeacherAssignment)
def assign_test_to_teacher(
    data: TestTeacherAssignmentCreate,
    session: Session = Depends(get_session),
    current_user: User = Depends(admin_required)
):
    assignment = TestTeacherAssignment(test_id=data.test_id, teacher_id=data.teacher_id)
    session.add(assignment)
    session.commit()
    session.refresh(assignment)
    return assignment


@router.get("/users/{user_id}/related", response_model=RelatedUsersOut)
def get_related_users(
    user_id: int = Path(..., ge=1),
    session: Session = Depends(get_session),
    current_user: User = Depends(admin_required),
):
    # Fetch the user by ID
    user = session.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    result = RelatedUsersOut()

    if user.role == "teacher":
        # Get students assigned to this teacher
        stmt = (
            select(User)
            .join(TeacherStudent, TeacherStudent.student_id == User.id)
            .where(TeacherStudent.teacher_id == user.id)
        )
        students = session.exec(stmt).all()
        result.students = students

    elif user.role == "student":
        # Get the teacher assigned to this student (expect one or none)
        stmt = (
            select(User)
            .join(TeacherStudent, TeacherStudent.teacher_id == User.id)
            .where(TeacherStudent.student_id == user.id)
        )
        teacher = session.exec(stmt).first()
        result.teacher = teacher

    return result



@router.post("/assign-teachers-to-classroom")
def assign_teachers_to_classroom(
    payload: dict,
    user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="Only admins can assign teachers")

    teacher_ids = payload.get("teacher_ids", [])
    classroom_id = payload.get("classroom_id")

    if not teacher_ids or not classroom_id:
        raise HTTPException(status_code=400, detail="Missing teacher_ids or classroom_id")

    existing_links = session.exec(
        select(ClassroomTeacherLink).where(
            ClassroomTeacherLink.classroom_id == classroom_id,
            ClassroomTeacherLink.teacher_id.in_(teacher_ids)
        )
    ).all()
    existing_ids = {link.teacher_id for link in existing_links}

    new_links = [
        ClassroomTeacherLink(classroom_id=classroom_id, teacher_id=tid)
        for tid in teacher_ids if tid not in existing_ids
    ]

    if not new_links:
        raise HTTPException(status_code=400, detail="All teachers already assigned")

    session.add_all(new_links)
    session.commit()
    return {"message": f"{len(new_links)} teacher(s) assigned successfully"}


@router.post("/assign-students-to-classroom")
def assign_students_to_classroom(
    payload: dict,
    user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="Only admins can assign students")

    student_ids = payload.get("student_ids", [])
    classroom_id = payload.get("classroom_id")

    if not student_ids or not classroom_id:
        raise HTTPException(status_code=400, detail="Missing student_ids or classroom_id")

    existing_links = session.exec(
        select(ClassroomStudentLink).where(
            ClassroomStudentLink.classroom_id == classroom_id,
            ClassroomStudentLink.student_id.in_(student_ids)
        )
    ).all()
    existing_ids = {link.student_id for link in existing_links}

    new_links = [
        ClassroomStudentLink(classroom_id=classroom_id, student_id=sid)
        for sid in student_ids if sid not in existing_ids
    ]

    if not new_links:
        raise HTTPException(status_code=400, detail="All students already assigned")

    session.add_all(new_links)
    session.commit()
    return {"message": f"{len(new_links)} students assigned successfully"}


