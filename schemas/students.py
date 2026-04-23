from typing import TYPE_CHECKING

from pydantic import BaseModel
from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from .references import ReferenceFace


# TODO GroupBase, GroupCreate, GroupUpdate, GroupPublic, GroupPublicWithStudents
class GroupBase(SQLModel):
    name: str = Field(index=True)
    potok: int = Field()

class Group(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)

    students: list["Student"] = Relationship(back_populates="group", cascade_delete=True)

class GroupCreate(GroupBase):
    pass

class GroupUpdate(BaseModel):
    name: str | None = None
    potok: int | None = None

class GroupPublic(GroupBase):
    id: int

class GroupPublicWithStudents(GroupPublic):
    students: list["StudentPublic"]


# TODO StudentBase, StudentCreate, StudentUpdate, StudentPublic, StudentPublicWithGroup, StudentPublicWithGroupAndReferences
class StudentBase(SQLModel):
    name: str = Field(index=True)
    group_id: int = Field(foreign_key="group.id", ondelete="CASCADE")
    telephone_number : str | None = Field()


class Student(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)

    group: "Group" = Relationship(back_populates="students")
    references: list["ReferenceFace"] = Relationship(back_populates="student", cascade_delete=True)

class StudentCreate(StudentBase):
    pass

class StudentUpdate(BaseModel):
    name: str | None = None
    group_id: int | None = None

class StudentPublic(StudentBase):
    id: int

class StudentPublicWithGroup(StudentPublic):
    group : GroupPublic

class StudentPublicWithGroupAndReferences(StudentPublicWithGroup):
    references:list["ReferenceFace"]