from contextlib import asynccontextmanager

from fastapi import FastAPI

from core.database import init_db
from api.students import router as students_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Создание БД и таблиц
    init_db()
    yield
    # Выполняется после завершения

app = FastAPI(lifespan=lifespan)
app.include_router(students_router)


@app.get("/")
async def root():
    return {"message": "Hello World"}


@app.get("/hello/{name}")
async def say_hello(name: str):
    return {"message": f"Hello {name}"}
