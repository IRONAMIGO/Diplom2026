from fastapi import APIRouter, Depends, Query, status, UploadFile, HTTPException
from sqlmodel import Session, select

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
    photos = session.exec(
        select(ReferenceFace).where(ReferenceFace.student_id == student_id).offset(offset).limit(limit)
    ).all()
    return photos

@references_router.post("/{student_id}/photos/", response_model=ReferenceFacePublic, status_code=status.HTTP_201_CREATED)
async def create_reference(*, session: Session = Depends(get_session), student_id: int, photo: UploadFile):
    """
    Создать фото студента:
    - **student_id** - id группы;
    - **photo** - файл с фотографией;
    """
    if photo.content_type not in ["image/jpeg", "image/png"]:
        raise HTTPException(status_code=status.HTTP_406_NOT_ACCEPTABLE, detail="Invalid file type")
    # TODO Обработка файла
    db_photo = ReferenceFace(student_id=student_id, embedding=b'111', image_path='path/to/image.jpg')
    session.add(db_photo)
    session.commit()
    session.refresh(db_photo)
    return db_photo