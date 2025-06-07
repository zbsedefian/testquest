# testquest/main.py
from fastapi import FastAPI
from routers import auth, student, teacher, admin, classroom, test
import models
from database import engine
from fastapi.staticfiles import StaticFiles

app = FastAPI()

app.mount("/uploaded_images", StaticFiles(directory="/Users/xed/Downloads/uploaded_images"), name="uploaded_images")

models.SQLModel.metadata.create_all(engine)

app.include_router(auth.router)
app.include_router(student.router)
app.include_router(teacher.router)
app.include_router(admin.router)
app.include_router(classroom.router)
app.include_router(test.router)