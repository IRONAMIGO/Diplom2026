import os
import uuid

from fastapi import APIRouter, Depends, Query, status, UploadFile, HTTPException
from sqlmodel import Session, select

from core.config import PHOTO_DIR
from core.database import get_session
from schemas.references import ReferenceFacePublic, ReferenceFace

references_router = APIRouter(
    prefix="/students",
    tags=["references"],
)

@references_router.get("/{student_id}/photos/", response_model=list[ReferenceFacePublic])
async def read_references(
        *,
        session: Session = Depends(get_session),
        student_id: int,
        offset: int = 0,
        limit: int = Query(default=20, le=20),
):
    references = session.exec(
        select(ReferenceFace).where(ReferenceFace.student_id == student_id).offset(offset).limit(limit)
    ).all()
    return references

@references_router.post("/{student_id}/photos/", response_model=ReferenceFacePublic, status_code=status.HTTP_201_CREATED)
async def create_reference(*, session: Session = Depends(get_session), student_id: int, photo: UploadFile):
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
    # Сохраняем загруженный файл на диск
    with open(file_path, "wb") as buffer:
        content = await photo.read()
        buffer.write(content)

    # TODO найти лицо на фото и создать эмбендинг

    # Создаём запись в БД
    db_reference = ReferenceFace(student_id=student_id, embedding=b'111', image_path=file_path)
    session.add(db_reference)
    session.commit()
    session.refresh(db_reference)
    return db_reference


@references_router.get("/{student_id}/photos/{photo_id}",
                       response_model=ReferenceFacePublic, )
async def read_reference(*, session: Session = Depends(get_session), student_id: int, photo_id: int):
    # TODO Проверка прав на действия
    reference = session.get(ReferenceFace, photo_id)
    if not reference:
        raise HTTPException(status_code=404, detail="Photo not found")
    return reference


@references_router.delete("/{student_id}/photos/{photo_id}")
async def delete_reference(*, session: Session = Depends(get_session), student_id: int, photo_id: int):
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