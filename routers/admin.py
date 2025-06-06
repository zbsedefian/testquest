from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Path, Body
from pydantic import BaseModel
from sqlalchemy import func
from sqlmodel import Session, select

from database import get_session
from dependencies import get_current_user
from models import User, Test


class UserCreate(BaseModel):
    username: str
    password: str
    role: str  # "teacher" or "student" or "admin"
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[str] = None


class UserUpdate(BaseModel):
    username: Optional[str] = None
    password: Optional[str] = None
    role: Optional[str] = None  # "teacher" or "student" or "admin"
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[str] = None


class UserOut(BaseModel):
    id: int
    username: str
    role: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[str] = None

    class Config:
        orm_mode = True


class PaginatedUsers(BaseModel):
    users: List[UserOut]
    total: int
    page: int
    total_pages: int
    per_page: int

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

    new_user = User(**data.model_dump())
    session.add(new_user)
    session.commit()
    session.refresh(new_user)
    return new_user



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

    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(user, key, value)

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

