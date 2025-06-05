# testquest/routers/auth.py
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlmodel import Session, select
from database import get_session
from models import User

router = APIRouter(prefix="/auth", tags=["auth"])

# Hardcoded users for MVP
dummy_users = [
    User(username="admin", password="admin", role="admin"),
    User(username="teacher", password="teacher", role="teacher"),
    User(username="student-01", password="student", role="student"),
    User(username="student-02", password="student", role="student")
]

class LoginRequest(BaseModel):
    username: str
    password: str

class LoginResponse(BaseModel):
    id: int
    username: str
    role: str

@router.post("/login", response_model=LoginResponse)
def login(data: LoginRequest, session: Session = Depends(get_session)):
    user = session.exec(select(User).where(User.username == data.username)).first()

    if not user:
        # Insert dummy user if not found
        user = next((u for u in dummy_users if u.username == data.username and u.password == data.password), None)
        if user:
            session.add(user)
            session.commit()
            session.refresh(user)
        else:
            raise HTTPException(status_code=401, detail="Invalid credentials")

    if user.password != data.password:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    return LoginResponse(id=user.id, username=user.username, role=user.role)



class SignupRequest(BaseModel):
    username: str
    password: str
    role: str  # "student", "teacher", or "admin"

class SignupResponse(BaseModel):
    id: int
    username: str
    role: str

@router.post("/signup", response_model=SignupResponse)
def signup(data: SignupRequest, session: Session = Depends(get_session)):
    # Check if username is already taken
    existing_user = session.exec(select(User).where(User.username == data.username)).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Username already exists")

    new_user = User(username=data.username, password=data.password, role=data.role)
    session.add(new_user)
    session.commit()
    session.refresh(new_user)

    return SignupResponse(id=new_user.id, username=new_user.username, role=new_user.role)
