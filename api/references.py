import os
import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query, status, UploadFile, HTTPException, Path
from sqlmodel import Session, select

from core.config import PHOTO_DIR, PHOTO_MAX_SIZE
from core.database import get_session
from core.image_utils import crop_face, read_image_bytes, write_image, reduce_image
from core.pipeline import FaceRecognitionPipeline
from schemas.references import ReferenceFacePublic, ReferenceFace

pipeline = None


def get_pipeline():
    global pipeline
    if pipeline is None:
        pipeline = FaceRecognitionPipeline()
    return pipeline


references_router = APIRouter(
    prefix="/students",
    tags=["references"],
)


@references_router.get("/{student_id}/photos/", response_model=list[ReferenceFacePublic])
async def read_references(
        *,
        session: Session = Depends(get_session),
        student_id: Annotated[int, Path(title="ID студента для получения фотографий")],
        offset: Annotated[int, Query(ge=0)] = 0,
        limit: Annotated[int, Query(le=20)] = 20
):
    references = session.exec(
        select(ReferenceFace).where(ReferenceFace.student_id == student_id).offset(offset).limit(limit)
    ).all()
    return references


@references_router.post("/{student_id}/photos/", response_model=ReferenceFacePublic,
                        status_code=status.HTTP_201_CREATED)
async def create_reference(
        *, session: Session = Depends(get_session),
        student_id: Annotated[int, Path(title="ID студента для добавления фотографии")],
        photo: UploadFile,
        pipe: FaceRecognitionPipeline = Depends(get_pipeline)
):
    """
    Создать фото студента:
    - **student_id** - id группы;
    - **photo** - файл с фотографией;
    """
    if photo.content_type not in ["image/jpeg", "image/png"]:
        raise HTTPException(status_code=status.HTTP_406_NOT_ACCEPTABLE, detail="Invalid file type")

    # Генерируем уникальное имя файла
    file_extension = ".jpg" if photo.content_type == "image/jpeg" else ".png"
    file_name = f"{uuid.uuid4()}{file_extension}"
    file_path = PHOTO_DIR / file_name
    # Убедимся, что директория для фото существует
    PHOTO_DIR.mkdir(parents=True, exist_ok=True)

    # Загружаем изображение
    img = read_image_bytes(await photo.read())

    # Детектируем лица
    boxes = pipe.detector.detect(img)
    if not boxes:
        raise ValueError("На изображении не найдено лицо")

    # Берём бокс с максимальной уверенностью
    best_box = max(boxes, key=lambda b: b[4])
    x1, y1, x2, y2, _ = best_box

    # Кроп
    face_crop = crop_face(img, (x1, y1, x2, y2))

    # Извлекаем эмбеддинг
    embedding = pipe.embedder.extract(face_crop)

    # Уменьшение размеров изображения (после извлечения всех необходимых данных)
    img_small, _ = reduce_image(img, PHOTO_MAX_SIZE)

    # Сохраняем изображение на диске
    write_image(file_path, img_small)

    # Создаём запись в БД
    db_reference = ReferenceFace(student_id=student_id, embedding=embedding, image_path=file_path)
    session.add(db_reference)
    session.commit()
    session.refresh(db_reference)
    return db_reference


@references_router.get("/{student_id}/photos/{photo_id}",
                       response_model=ReferenceFacePublic, )
async def read_reference(
        *, session: Session = Depends(get_session),
        student_id: Annotated[int, Path(title="ID студента для получения фотографии")],
        photo_id: Annotated[int, Path(title="ID фотографии для получения")]
):
    # TODO Проверка прав на действия
    reference = session.get(ReferenceFace, photo_id)
    if not reference:
        raise HTTPException(status_code=404, detail="Photo not found")
    return reference


@references_router.delete("/{student_id}/photos/{photo_id}")
async def delete_reference(
        *, session: Session = Depends(get_session),
        student_id: Annotated[int, Path(title="ID студента для удаления фотографии")],
        photo_id: Annotated[int, Path(title="ID фотографии для удаления")]
):
    # TODO Проверить права пользователя на удаление
    reference = session.get(ReferenceFace, photo_id)
    if not reference:
        raise HTTPException(status_code=404, detail="Photo not found")
    if os.path.exists(f"{reference.image_path}"):
        os.remove(f'{reference.image_path}')
    session.delete(reference)
    session.commit()
    # TODO Перестроить faiss индекс
    return {"ok": True}
