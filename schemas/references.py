from datetime import date
from typing import TYPE_CHECKING

from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from .students import Student


class ReferenceFaceBase(SQLModel):
    student_id: int = Field(foreign_key="student.id", index=True, ondelete="CASCADE")


class ReferenceFace(ReferenceFaceBase, table=True):
    id: int | None = Field(default=None, primary_key=True)
    embedding: bytes = Field()      # бинарное представление np.float32
    image_path: str = Field()       # путь к сохранённому изображению эталона
    created_at: date = Field(default_factory=date.today)

    student: "Student" = Relationship(back_populates="references")


class ReferenceFaceCreate(ReferenceFaceBase):
    pass


class ReferenceFacePublic(ReferenceFaceBase):
    id: int
    image_path: str
    created_at: date


class ReferenceFacePublicWithStudent(ReferenceFacePublic):
    student: "Student"
