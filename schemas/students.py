from typing import TYPE_CHECKING

from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from .references import ReferenceFace


# TODO GroupBase, GroupCreate, GroupUpdate, GroupPublic, GroupPublicWithStudents

class Group(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    name: str = Field(index=True)

    students: list["Student"] = Relationship(back_populates="group", cascade_delete=True)


# TODO StudentBase, StudentCreate, StudentUpdate, StudentPublic, StudentPublicWithGroup, StudentPublicWithGroupAndReferences

class Student(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    name: str = Field(index=True)
    group_id: int = Field(foreign_key="group.id", ondelete="CASCADE")

    group: "Group" = Relationship(back_populates="students")
    references: list["ReferenceFace"] = Relationship(back_populates="student", cascade_delete=True)