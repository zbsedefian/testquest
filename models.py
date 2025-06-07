from typing import Optional
from sqlmodel import SQLModel, Field
from datetime import datetime


class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    username: str = Field(index=True, nullable=False, unique=True)
    password: str  # plaintext for MVP only; use hashed in production
    role: str = Field(nullable=False, description="admin, teacher, or student")
    first_name: Optional[str] = Field(default=None)
    last_name: Optional[str] = Field(default=None)
    email: Optional[str] = Field(default=None)
    created_at: datetime = Field(default_factory=datetime.utcnow)


class Test(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(nullable=False)
    description: Optional[str] = Field(default="", description="Optional test description")
    created_by: int = Field(foreign_key="user.id", nullable=False)

    is_timed: bool = Field(default=False)
    duration_minutes: Optional[int] = Field(default=None, description="Test duration in minutes if timed")
    max_attempts: Optional[int] = Field(default=1, description="Maximum number of allowed attempts")

    available_from: Optional[datetime] = Field(default=None, description="When test becomes accessible")
    available_until: Optional[datetime] = Field(default=None, description="When test expires")
    is_published: bool = Field(default=False, description="Controls visibility in selection menus")

    show_results_immediately: bool = Field(default=True)
    allow_back_navigation: bool = Field(default=True)
    shuffle_questions: bool = Field(default=False)
    pass_score: Optional[float] = Field(default=None, description="Pass mark as percentage (e.g., 70.0)")
    graded_by: str = Field(default="auto", description="auto or manual")
    created_at: datetime = Field(default_factory=datetime.utcnow)


class Question(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    test_id: int = Field(foreign_key="test.id", nullable=False)
    order: int = Field(default=0, description="Question order within the test")
    question_text: str = Field(nullable=False)
    choices: str = Field(nullable=False, description="JSON string of choices (A-D)")
    correct_choice: str = Field(nullable=False)
    explanation: str = Field(nullable=False)
    requires_manual_grading: bool = Field(default=False, description="Set to true for essay/open questions")
    image_url: Optional[str] = Field(default=None, description="Optional URL to image file")


class StudentAnswer(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    student_id: int = Field(foreign_key="user.id", nullable=False)
    question_id: int = Field(foreign_key="question.id", nullable=False)
    selected_choice: str = Field(nullable=False)
    is_correct: bool = Field(default=False)
    submitted_at: datetime = Field(default_factory=datetime.utcnow)
    manual_score: Optional[float] = Field(default=None, description="Score from manual grading if applicable")
    feedback: Optional[str] = Field(default=None, description="Optional feedback for the answer")


class TestResult(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    student_id: int = Field(foreign_key="user.id", nullable=False)
    test_id: int = Field(foreign_key="test.id", nullable=False)
    score: float = Field(nullable=False)
    completed_at: Optional[datetime] = Field(default_factory=datetime.utcnow)
    attempt_number: Optional[int] = Field(default=1)


class Classroom(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(nullable=False)
    created_at: datetime = Field(default_factory=datetime.utcnow)


class ClassroomTeacherLink(SQLModel, table=True):
    classroom_id: int = Field(foreign_key="classroom.id", primary_key=True)
    teacher_id: int = Field(foreign_key="user.id", primary_key=True)


class ClassroomStudentLink(SQLModel, table=True):
    classroom_id: int = Field(foreign_key="classroom.id", primary_key=True)
    student_id: int = Field(foreign_key="user.id", primary_key=True)


class ClassroomTestAssignment(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    classroom_id: int = Field(foreign_key="classroom.id", nullable=False)
    test_id: int = Field(foreign_key="test.id", nullable=False)
    assigned_date: datetime = Field(default_factory=datetime.utcnow)
    available_from: Optional[datetime] = Field(default=None)
    available_until: Optional[datetime] = Field(default=None)
    visible: bool = Field(default=True, description="If false, students won’t see it yet")


class PasswordResetToken(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id")
    token: str
    expires_at: datetime = Field(default_factory=lambda: datetime.utcnow() + timedelta(hours=1))
