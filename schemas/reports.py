from datetime import date
from typing import TYPE_CHECKING, Optional

from sqlmodel import SQLModel, Field, Relationship

from .students import StudentPublic
if TYPE_CHECKING:
    from .students import Student


class RecognitionDataBase(SQLModel):
    lecture_date: date = Field(default_factory=date.today)
    lecture_num: int = Field()  # номер в расписании


class RecognitionData(RecognitionDataBase, table=True):
    id: int | None = Field(default=None, primary_key=True)
    image_path: str = Field()  # путь к сохранённому изображению

    results: list["RecognitionResult"] = Relationship(back_populates="data", cascade_delete=True)


class RecognitionDataCreate(RecognitionDataBase):
    pass


class RecognitionDataUpdate(SQLModel):
    lecture_date: date | None = None
    lecture_num: int | None = None


class RecognitionDataPublic(RecognitionDataBase):
    id: int
    image_path: str


class RecognitionDataPublicWithRecognitionResultAndStudent(RecognitionDataPublic):
    results: list["RecognitionResultPublicWithStudent"]


class RecognitionResultBase(SQLModel):
    student_id: int | None = Field(default=None, index=True, foreign_key="student.id",
                                   ondelete="SET NULL")  # None если не распознан
    data_id: int = Field(foreign_key="recognitiondata.id", ondelete="CASCADE")
    bbox_x1: float = Field()
    bbox_y1: float = Field()
    bbox_x2: float = Field()
    bbox_y2: float = Field()
    confidence: float = Field()  # уверенность детекции
    similarity: float | None = Field(default=None)  # косинусное сходство с эталоном


class RecognitionResult(RecognitionResultBase, table=True):
    id: int | None = Field(default=None, primary_key=True)

    data: "RecognitionData" = Relationship(back_populates="results")
    student: Optional["Student"] = Relationship(back_populates="results")


class RecognitionResultCreate(RecognitionResultBase):
    reference_db_id: int | None


class RecognitionResultUpdate(SQLModel):
    student_id: int | None = None
    similarity: None = None  # при ручном вмешательстве обнуляем сходство


class RecognitionResultPublic(RecognitionResultBase):
    id: int


class RecognitionResultPublicWithStudent(RecognitionResultPublic):
    student: Optional["StudentPublic"] = None
