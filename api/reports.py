import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query, status, Form, UploadFile, HTTPException
from sqlmodel import Session, select

from core.config import REPORT_DIR, REPORT_MAX_SIZE
from core.database import get_session
from core.image_utils import read_image_bytes, reduce_image, write_image
from core.pipeline import FaceRecognitionPipeline
from schemas.references import ReferenceFace
from schemas.reports import RecognitionResultPublic, RecognitionResult, RecognitionDataCreate, RecognitionData, \
    RecognitionDataPublic

pipeline = None
def get_pipeline():
    global pipeline
    if pipeline is None:
        pipeline = FaceRecognitionPipeline()
    return pipeline

reports_router = APIRouter(
    prefix="/reports",
    tags=["reports"],
)


@reports_router.get("/", response_model=list[RecognitionResultPublic])
async def read_results(
        *,
        session: Session = Depends(get_session),
        offset: int = 0,
        limit: int = Query(default=10, le=10),
):
    results = session.exec(select(RecognitionResult).offset(offset).limit(limit)).all()
    return results


@reports_router.post("/recognize", response_model=list[RecognitionResultPublic], status_code=status.HTTP_201_CREATED)
async def create_results(
        *, session: Session = Depends(get_session),
        data: Annotated[RecognitionDataCreate, Form()],
        photo: UploadFile,
        pipe: FaceRecognitionPipeline = Depends(get_pipeline)
):
    """
    Отправить групповое фото на распознавание:
    - **lecture_date** - дата;
    - **lecture_num** - номер в рассписании;
    - **photo** - файл с фотографией;
    """
    if photo.content_type not in ["image/jpeg", "image/png"]:
        raise HTTPException(status_code=status.HTTP_406_NOT_ACCEPTABLE, detail="Invalid file type")

    # Генерируем уникальное имя файла
    file_extension = ".jpg" if photo.content_type == "image/jpeg" else ".png"
    file_name = f"{uuid.uuid4()}{file_extension}"
    file_path = REPORT_DIR / file_name
    # Убедимся, что директория существует
    REPORT_DIR.mkdir(parents=True, exist_ok=True)

    # Загружаем изображение
    img = read_image_bytes(await photo.read())
    # Уменьшенное изображение для сохранения
    img_small, scale = reduce_image(img, REPORT_MAX_SIZE)
    # Сохраняем изображение на диске
    write_image(file_path, img_small)

    # Сохраняем данные в БД
    data = RecognitionDataCreate.model_validate(data)
    db_data = RecognitionData(lecture_date=data.lecture_date, lecture_num=data.lecture_num, image_path=file_path)
    session.add(db_data)
    session.commit()
    session.refresh(db_data)
    db_data = RecognitionDataPublic.model_validate(db_data)

    # Определяем присутствующих на фото
    results = pipe.recognize_group_image(db_data.id, img, scale)
    if not results:
        raise ValueError("На изображении не найдено лиц")
    db_results = []
    for result in results:
        db_result = RecognitionResult.model_validate(result)
        student_id = None
        ref = session.get(ReferenceFace, result.reference_id)
        if ref:
            student_id = ref.student_id
        db_result.student_id = student_id
        session.add(db_result)
        session.commit()
        session.refresh(db_result)
        db_results.append(db_result)
    return db_results
