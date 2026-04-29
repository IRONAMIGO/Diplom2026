from contextlib import asynccontextmanager

from fastapi import FastAPI

from api.references import references_router
from api.reports import reports_router
from api.students import students_router, groups_router, streams_router
from core.database import init_db
from core.pipeline import FaceRecognitionPipeline

# Глобальный объект пайплайна для загрузки моделей при старте
pipeline = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global pipeline
    # Создание БД и таблиц
    init_db()
    # Предварительная загрузка моделей и индекса
    pipeline = FaceRecognitionPipeline()
    yield
    # Выполняется после завершения

app = FastAPI(lifespan=lifespan)
app.include_router(streams_router)
app.include_router(groups_router)
app.include_router(students_router)
app.include_router(references_router)
app.include_router(reports_router)


@app.get("/")
async def root():
    return {"message": "Hello World"}


@app.get("/hello/{name}")
async def say_hello(name: str):
    return {"message": f"Hello {name}"}
