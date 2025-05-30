# testquest/dependencies.py
from fastapi import Header, HTTPException, Depends
from sqlmodel import Session, select
from database import get_session
from models import User

def get_current_user(
    x_user_id: int = Header(...),
    x_user_role: str = Header(...),
    session: Session = Depends(get_session),
) -> User:
    user = session.exec(
        select(User).where(User.id == x_user_id, User.role == x_user_role)
    ).first()
    if not user:
        raise HTTPException(status_code=401, detail="Invalid user or role in headers")
    return user
