import uuid
from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, Query, status, Form, UploadFile, HTTPException, Response, File, Path, Security
from sqlmodel import Session, select, col, func

from core.config import REPORT_DIR, REPORT_MAX_SIZE, BASE_DIR
from core.database import get_session
from core.image_utils import read_image_bytes, reduce_image, write_image
from core.pipeline import FaceRecognitionPipeline
from core.auth import get_current_user
from schemas.users import User
from schemas.references import ReferenceFace
from schemas.reports import RecognitionResult, RecognitionDataCreate, RecognitionData, \
    RecognitionDataPublic, RecognitionDataPublicWithRecognitionResultAndStudent, RecognitionResultPublicWithStudent, \
    RecognitionResultUpdate
from schemas.students import Group, Student

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


@reports_router.get("/", response_model=list[RecognitionDataPublicWithRecognitionResultAndStudent])
async def read_results(
        *, response: Response,
        session: Session = Depends(get_session),
        lecture_date: Annotated[date | None, Query()] = None,
        lecture_num: Annotated[int | None, Query()] = None,
        stream_id: Annotated[int | None, Query()] = None,
        group_id: Annotated[int | None, Query()] = None,
        student_id: Annotated[int | None, Query()] = None,
        offset: Annotated[int | None, Query(ge=0)] = None,
        limit: Annotated[int | None, Query(gt=0, le=25)] = None,
        current_user: User = Security(get_current_user, scopes=[])  # любой аутентифицированный
):
    # Базовый запрос
    base_stmt = select(RecognitionData)
    # Подсчёт количества
    count_stmt = select(func.count(func.distinct(RecognitionData.id))).select_from(RecognitionData)
    if lecture_date:
        base_stmt = base_stmt.where(RecognitionData.lecture_date == lecture_date)
        count_stmt = count_stmt.where(RecognitionData.lecture_date == lecture_date)
    if lecture_num:
        base_stmt = base_stmt.where(RecognitionData.lecture_num == lecture_num)
        count_stmt = count_stmt.where(RecognitionData.lecture_num == lecture_num)
    if student_id:
        base_stmt = base_stmt.join(RecognitionResult).where(RecognitionResult.student_id == student_id)
        count_stmt = count_stmt.join(RecognitionResult).where(RecognitionResult.student_id == student_id)
    elif group_id:
        base_stmt = base_stmt.join(RecognitionResult).join(Student).where(Student.group_id == group_id)
        count_stmt = count_stmt.join(RecognitionResult).join(Student).where(Student.group_id == group_id)
    elif stream_id:
        base_stmt = base_stmt.join(RecognitionResult).join(Student).join(Group).where(Group.stream_id == stream_id)
        count_stmt = count_stmt.join(RecognitionResult).join(Student).join(Group).where(Group.stream_id == stream_id)
    base_stmt = base_stmt.group_by(RecognitionData.id)
    total = session.exec(count_stmt).one()
    response.headers["X-Total-Count"] = str(total)
    if offset:
        base_stmt = base_stmt.offset(offset)
    if limit:
        base_stmt = base_stmt.limit(limit)
    results = session.exec(base_stmt).all()
    return results


@reports_router.post("/", response_model=RecognitionDataPublic,
                     status_code=status.HTTP_201_CREATED)
async def create_result(
        *, session: Session = Depends(get_session),
        data: Annotated[RecognitionDataCreate | str, Form()],
        photo: Annotated[UploadFile, File()],
        pipe: FaceRecognitionPipeline = Depends(get_pipeline),
        current_user: User = Security(get_current_user, scopes=["teacher", "admin"])  # teacher или admin
):
    """
    Отправить групповое фото на распознавание:
    - **lecture_date** - дата;
    - **lecture_num** - номер в расписании;
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

    # Относительный путь от BASE_DIR (для хранения в БД)
    file_db_path = "/" + str(file_path.relative_to(BASE_DIR)).replace("\\","/")

    # Загружаем изображение
    img = read_image_bytes(await photo.read())
    # Уменьшенное изображение для сохранения
    img_small, scale = reduce_image(img, REPORT_MAX_SIZE)
    # Сохраняем изображение на диске
    write_image(file_path, img_small)

    # Сохраняем данные в БД
    if type(data) is str:
        # Парсим JSON-строку в объект RecognitionDataCreate
        parsed_data = RecognitionDataCreate.model_validate_json(data)
        db_data = RecognitionData(lecture_date=parsed_data.lecture_date, lecture_num=parsed_data.lecture_num,
                                  image_path=file_db_path)
    else:
        data = RecognitionDataCreate.model_validate(data)
        db_data = RecognitionData(lecture_date=data.lecture_date, lecture_num=data.lecture_num, image_path=file_db_path)
    session.add(db_data)
    session.commit()
    session.refresh(db_data)
    db_data = RecognitionDataPublic.model_validate(db_data)

    # Определяем присутствующих на фото
    results = pipe.recognize_group_image(db_data.id, img, scale)
    if not results:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="На изображении не найдено лиц"
        )
    db_results = []
    for result in results:
        db_result = RecognitionResult.model_validate(result)
        student_id = None
        if result.reference_db_id is not None:
            ref = session.get(ReferenceFace, result.reference_db_id)
            if ref:
                student_id = ref.student_id
        db_result.student_id = student_id
        session.add(db_result)
        session.commit()
        session.refresh(db_result)
        db_results.append(db_result)
    return db_data


@reports_router.get("/{data_id}", response_model=RecognitionDataPublicWithRecognitionResultAndStudent)
async def read_report(
        *, session: Session = Depends(get_session),
        data_id: Annotated[int, Path(title="ID отчета для получения")],
        current_user: User = Security(get_current_user, scopes=[])
):
    recognition_data = session.get(RecognitionData, data_id)
    if not recognition_data:
        raise HTTPException(status_code=404, detail="Report not found")
    return recognition_data


@reports_router.put("/results/{result_id}", response_model=RecognitionResultPublicWithStudent)
async def update_result(
        *, session: Session = Depends(get_session),
        result_id: Annotated[int, Path(title="ID результата для изменения")],
        result: Annotated[RecognitionResultUpdate, Form()],
        current_user: User = Security(get_current_user, scopes=["teacher", "admin"])  # teacher или admin
):
    db_result = session.get(RecognitionResult, result_id)
    if not db_result:
        raise HTTPException(status_code=404, detail="Result not found")
    result_update_data = result.model_dump(exclude_unset=True)
    result_update_data["similarity"] = None
    db_result.sqlmodel_update(result_update_data)
    session.add(db_result)
    session.commit()
    session.refresh(db_result)
    return db_result
