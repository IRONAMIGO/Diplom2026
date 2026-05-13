from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from api.references import references_router
from api.reports import reports_router
from api.students import students_router, groups_router, streams_router
from api.users import token_router, users_router
from core.config import CORS_URL
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

# Разрешаем доступ с определенных доменов
app.add_middleware(
    CORSMiddleware,
    allow_origins=[CORS_URL,
                   "http://localhost:5173",
                   "http://127.0.0.1:5173",
                   "http://0.0.0.0:8080",
                   "http://localhost:8080",
                   "http://127.0.0.1:8080",
                   "http://localhost:80",
                   "http://127.0.0.1:80",
                   "http://localhost",
                   "http://127.0.0.1",
                   ],  # Разрешенные источники
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],  # Разрешенные методы
    allow_headers=["*"],  # Разрешенные заголовки
    expose_headers=["X-Total-Count"],
)

app.include_router(streams_router)
app.include_router(groups_router)
app.include_router(students_router)
app.include_router(references_router)
app.include_router(reports_router)
app.include_router(token_router)
app.include_router(users_router)

app.mount("/data", StaticFiles(directory="data"), name="data")
