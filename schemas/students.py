from typing import TYPE_CHECKING, Optional

from pydantic import BaseModel
from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from .references import ReferenceFace
    from .users import User


class StreamBase(SQLModel):
    name: str = Field(index=True)


class Stream(StreamBase, table=True):
    id: int | None = Field(default=None, primary_key=True)

    groups: list["Group"] = Relationship(back_populates="stream", cascade_delete=True)
    user: Optional["User"] = Relationship(back_populates="stream")


class StreamCreate(StreamBase):
    pass


class StreamUpdate(BaseModel):
    name :str


class StreamPublic(StreamBase):
    id: int


# ========== Group Schemas ==========
class GroupBase(SQLModel):
    name: str = Field(index=True)
    stream_id: int = Field(foreign_key="stream.id", ondelete="CASCADE")


class Group(GroupBase, table=True):
    id: int | None = Field(default=None, primary_key=True)

    stream: "Stream" = Relationship(back_populates="groups")
    students: list["Student"] = Relationship(back_populates="group", cascade_delete=True)
    user: Optional["User"] = Relationship(back_populates='group')


class GroupCreate(GroupBase):
    pass


class GroupUpdate(BaseModel):
    name: str | None = None
    stream: int | None = None


class GroupPublic(GroupBase):
    id: int


class GroupPublicWithStudents(GroupPublic):
    students: list["StudentPublic"]


# ========== Student Schemas ==========
class StudentBase(SQLModel):
    name: str = Field(index=True)
    group_id: int = Field(foreign_key="group.id", ondelete="CASCADE")
    phone_number: str | None = Field()
    email: str | None = Field()


class Student(StudentBase, table=True):
    id: int | None = Field(default=None, primary_key=True)

    group: "Group" = Relationship(back_populates="students")
    references: list["ReferenceFace"] = Relationship(back_populates="student", cascade_delete=True)
    user: Optional["User"] = Relationship(back_populates="student")


class StudentCreate(StudentBase):
    pass


class StudentUpdate(BaseModel):
    name: str | None = None
    group_id: int | None = None
    phone_number: str | None = None
    email: str | None = None


class StudentPublic(StudentBase):
    id: int


class StudentPublicWithGroup(StudentPublic):
    group: GroupPublic


class StudentPublicWithGroupAndReferences(StudentPublicWithGroup):
    references: list["ReferenceFace"]
