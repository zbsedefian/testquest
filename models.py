# testquest/models.py
from typing import Optional
from sqlmodel import SQLModel, Field, Relationship
from datetime import datetime

class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    username: str
    password: str  # plaintext for MVP ONLY
    role: str  # 'admin', 'teacher', 'student'

class Test(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    created_by: int = Field(foreign_key="user.id")

class Question(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    test_id: int = Field(foreign_key="test.id")
    order: int = Field(default=0)  # question order within the test
    question_text: str
    choices: str  # JSON string of choices A-D
    correct_choice: str
    explanation: str

class StudentAnswer(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    student_id: int = Field(foreign_key="user.id")
    question_id: int = Field(foreign_key="question.id")
    selected_choice: str
    is_correct: bool

class TestResult(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    student_id: int = Field(foreign_key="user.id")
    test_id: int = Field(foreign_key="test.id")
    score: int
    completed_at: Optional[str]

class TeacherStudent(SQLModel, table=True):
    teacher_id: int = Field(foreign_key="user.id", primary_key=True)
    student_id: int = Field(foreign_key="user.id", primary_key=True)

class StudentTestAssignment(SQLModel, table=True):
    student_id: int = Field(foreign_key="user.id", primary_key=True)
    test_id: int = Field(foreign_key="test.id", primary_key=True)
    assigned_date: datetime = Field(default_factory=datetime.utcnow)
    completed_date: Optional[datetime] = None
    score: Optional[float] = None  # could be percent or points
    started: bool = Field(default=False)
    finished: bool = Field(default=False)

class TestTeacherAssignment(SQLModel, table=True):
    id: int = Field(default=None, primary_key=True)
    test_id: int = Field(foreign_key="test.id")
    teacher_id: int = Field(foreign_key="user.id")
