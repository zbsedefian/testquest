from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlmodel import Session, select

from dependencies import get_current_user
from models import Classroom, ClassroomStudentLink, User, StudentTestAssignment
from database import get_session

router = APIRouter()

@router.post("/tests/{test_id}/assign-to-classroom/{classroom_id}")
def assign_test_to_classroom(test_id: int, classroom_id: int, session: Session = Depends(get_session)):
    statement = select(ClassroomStudentLink).where(ClassroomStudentLink.classroom_id == classroom_id)
    links = session.exec(statement).all()
    if not links:
        raise HTTPException(status_code=404, detail="No students in classroom.")
    for link in links:
        assignment = StudentTestAssignment(test_id=test_id, student_id=link.student_id)
        session.add(assignment)
    session.commit()
    return {"message": "Test assigned to all students in classroom."}
