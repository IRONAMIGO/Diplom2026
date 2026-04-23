from datetime import date
from typing import TYPE_CHECKING

from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from .students import Student


# TODO ReferenceFaceBase, ReferenceFaceCreate, ReferenceFaceUpdate, ReferenceFacePublic, ReferenceFacePublicWithStudent

class ReferenceFace(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    student_id: int = Field(foreign_key="student.id", index=True, ondelete="CASCADE")
    embedding: bytes = Field()                          # бинарное представление np.float32
    image_path: str                                     # путь к сохранённому изображению эталона
    created_at: date = Field(default_factory=date.today)

    student: "Student" = Relationship(back_populates="references")
