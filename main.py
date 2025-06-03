# testquest/main.py
from fastapi import FastAPI
from routers import auth, student, teacher, admin, classroom
import models
from database import engine

app = FastAPI()

models.SQLModel.metadata.create_all(engine)

app.include_router(auth.router)
app.include_router(student.router)
app.include_router(teacher.router)
app.include_router(admin.router)
app.include_router(classroom.router)