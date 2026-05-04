from typing import Annotated

from fastapi import APIRouter, HTTPException, Depends, Query, status, Form, Path
from sqlmodel import Session, select

from core.database import get_session
from schemas.students import StudentUpdate, StudentPublic, Student, StudentCreate, GroupPublic, Group, GroupCreate, \
    GroupUpdate, Stream, StreamUpdate, StreamPublic, StreamCreate, StudentPublicWithGroup

# <editor-fold desc="streams_router">
streams_router = APIRouter(
    prefix="/streams",
    tags=["streams"],
)


@streams_router.get("/", response_model=list[StreamPublic])
async def read_streams(
        *,
        session: Session = Depends(get_session),
        offset: int = 0,
        limit: int = Query(default=10, le=10),
):
    streams = session.exec(select(Stream).offset(offset).limit(limit)).all()
    return streams


@streams_router.post("/", response_model=StreamPublic, status_code=status.HTTP_201_CREATED)
async def create_stream(
        *, session: Session = Depends(get_session),
        stream: Annotated[StreamCreate, Form()]
):
    """
    Создать группу:
    - **name** - имя группы;
    - **stream_id** - id потока;
    """
    db_stream = Stream.model_validate(stream)
    session.add(db_stream)
    session.commit()
    session.refresh(db_stream)
    return db_stream


@streams_router.get("/{stream_id}",
                    response_model=StreamPublic, )
async def read_stream(
        *, session: Session = Depends(get_session),
        stream_id: Annotated[int, Path(title="ID потока для получения")]
):
    stream = session.get(Stream, stream_id)
    if not stream:
        raise HTTPException(status_code=404, detail="Stream not found")
    return stream


@streams_router.put("/{stream_id}", response_model=StreamPublic)
async def update_stream(
        *, session: Session = Depends(get_session),
        stream_id: Annotated[int, Path(title="ID потока для изменения")],
        stream: Annotated[StreamUpdate, Form()]
):
    db_stream = session.get(Stream, stream_id)
    if not db_stream:
        raise HTTPException(status_code=404, detail="Stream not found")
    stream_update_data = stream.model_dump(exclude_unset=True)
    db_stream.sqlmodel_update(stream_update_data)
    session.add(db_stream)
    session.commit()
    session.refresh(db_stream)
    return db_stream


@streams_router.delete("/{stream_id}")
async def delete_stream(
        *, session: Session = Depends(get_session),
        stream_id: Annotated[int, Path(title="ID потока для удаления")]
):
    stream = session.get(Stream, stream_id)
    if not stream:
        raise HTTPException(status_code=404, detail="Stream not found")
    # TODO При удалении потока удаляются группы, студенты, референсы. Предусмотреть удаление файлов эталонных фото.
    session.delete(stream)
    session.commit()
    return {"ok": True}
# </editor-fold>


# <editor-fold desc="groups_router">
groups_router = APIRouter(
    prefix="/groups",
    tags=["groups"],
)


@groups_router.get("/", response_model=list[GroupPublic])
async def read_groups(
        *,
        session: Session = Depends(get_session),
        stream_id: Annotated[int | None, Query()] = None,
        offset: int = 0,
        limit: int = Query(default=10, le=10),
):
    statement = select(Group)
    if stream_id:
        statement = statement.where(Group.stream_id == stream_id)
    groups = session.exec(statement.offset(offset).limit(limit)).all()
    return groups


@groups_router.post("/", response_model=GroupPublic, status_code=status.HTTP_201_CREATED)
async def create_group(
        *, session: Session = Depends(get_session),
        group: Annotated[GroupCreate, Form()]
):
    """
    Создать группу:
    - **name** - имя группы;
    - **stream_id** - id потока;
    """
    db_group = Group.model_validate(group)
    session.add(db_group)
    session.commit()
    session.refresh(db_group)
    return db_group


@groups_router.get("/{group_id}",
                   response_model=GroupPublic, )
async def read_group(
        *, session: Session = Depends(get_session),
        group_id: Annotated[int, Path(title="ID группы для получения")]
):
    group = session.get(Group, group_id)
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")
    return group


@groups_router.put("/{group_id}", response_model=GroupPublic)
async def update_group(
        *, session: Session = Depends(get_session),
        group_id: Annotated[int, Path(title="ID группы для изменения")],
        group: Annotated[GroupUpdate, Form()]
):
    db_group = session.get(Group, group_id)
    if not db_group:
        raise HTTPException(status_code=404, detail="Group not found")
    group_update_data = group.model_dump(exclude_unset=True)
    db_group.sqlmodel_update(group_update_data)
    session.add(db_group)
    session.commit()
    session.refresh(db_group)
    return db_group


@groups_router.delete("/{group_id}")
async def delete_group(
        *, session: Session = Depends(get_session),
        group_id: Annotated[int, Path(title="ID группы для удаления")]
):
    group = session.get(Group, group_id)
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")
    # TODO При удалении группы удаляются студенты, референсы. Предусмотреть удаление файлов эталонных фото.
    session.delete(group)
    session.commit()
    return {"ok": True}
# </editor-fold>


# <editor-fold desc="students_router">
students_router = APIRouter(
    prefix="/students",
    tags=["students"],
)


@students_router.get("/", response_model=list[StudentPublicWithGroup])
async def read_students(
        *,
        session: Session = Depends(get_session),
        group_id: Annotated[int | None, Query()] = None,
        offset: Annotated[int, Query(ge=0)] = 0,
        limit: Annotated[int, Query(le=20)] = 20
):
    statement = select(Student)
    if group_id:
        statement = statement.where(Student.group_id == group_id)
    students = session.exec(statement.offset(offset).limit(limit)).all()
    return students


@students_router.post("/", response_model=StudentPublic, status_code=status.HTTP_201_CREATED)
async def create_student(
        *, session: Session = Depends(get_session),
        student: Annotated[StudentCreate, Form()]
):
    """
    Создать студента:
    - **name** - имя и фамилия;
    - **group_id** - id группы;
    - **phone_number** - номер телефона (необязательный);
    - **email** - электронная почта (необязательный);
    """
    db_student = Student.model_validate(student)
    session.add(db_student)
    session.commit()
    session.refresh(db_student)
    return db_student


@students_router.get("/{student_id}",
                     response_model=StudentPublic, )
async def read_student(
        *, session: Session = Depends(get_session),
        student_id: Annotated[int, Path(title="ID студента для получения")]
):
    student = session.get(Student, student_id)
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    return student


@students_router.put("/{student_id}", response_model=StudentPublic)
async def update_student(
        *, session: Session = Depends(get_session),
        student_id: Annotated[int, Path(title="ID студента для изменения")],
        student: Annotated[StudentUpdate, Form()]
):
    db_student = session.get(Student, student_id)
    if not db_student:
        raise HTTPException(status_code=404, detail="Student not found")
    student_update_data = student.model_dump(exclude_unset=True)
    db_student.sqlmodel_update(student_update_data)
    session.add(db_student)
    session.commit()
    session.refresh(db_student)
    return db_student


@students_router.delete("/{student_id}")
async def delete_student(
        *, session: Session = Depends(get_session),
        student_id: Annotated[int, Path(title="ID студента для удаления")]
):
    student = session.get(Student, student_id)
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    # TODO При удалении студента удаляются референсы. Предусмотреть удаление файлов эталонных фото.
    session.delete(student)
    session.commit()
    return {"ok": True}
# </editor-fold>
