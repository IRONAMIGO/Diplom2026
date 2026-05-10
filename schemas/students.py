from typing import TYPE_CHECKING, Optional

from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from .references import ReferenceFace, ReferenceFacePublic
    from .users import User
    from .reports import RecognitionResult, RecognitionResultPublic


# <editor-fold desc="Stream Schemas">
class StreamBase(SQLModel):
    name: str = Field(index=True)


class Stream(StreamBase, table=True):
    id: int | None = Field(default=None, primary_key=True)

    groups: list["Group"] = Relationship(back_populates="stream", cascade_delete=True)
    users: list["User"] = Relationship(back_populates="stream")


class StreamCreate(StreamBase):
    pass


class StreamUpdate(SQLModel):
    pass


class StreamPublic(StreamBase):
    id: int
# </editor-fold>


# <editor-fold desc="Group Schemas">
class GroupBase(SQLModel):
    name: str = Field(index=True)
    stream_id: int = Field(foreign_key="stream.id", ondelete="CASCADE")


class Group(GroupBase, table=True):
    id: int | None = Field(default=None, primary_key=True)

    stream: "Stream" = Relationship(back_populates="groups")
    students: list["Student"] = Relationship(back_populates="group", cascade_delete=True)
    users: list["User"] = Relationship(back_populates='group')


class GroupCreate(GroupBase):
    pass


class GroupUpdate(SQLModel):
    name: str | None = None
    stream_id: int | None = None


class GroupPublic(GroupBase):
    id: int


class GroupPublicWithStudents(GroupPublic):
    students: list["StudentPublic"]


class GroupPublicWithStream(GroupPublic):
    stream: "StreamPublic"
# </editor-fold>


# <editor-fold desc="Student Schemas">
class StudentBase(SQLModel):
    name: str = Field(index=True)
    group_id: int = Field(foreign_key="group.id", ondelete="CASCADE")


class Student(StudentBase, table=True):
    id: int | None = Field(default=None, primary_key=True)
    phone_number: str | None = Field(default=None)
    email: str | None = Field(default=None)

    group: "Group" = Relationship(back_populates="students")
    references: list["ReferenceFace"] = Relationship(back_populates="student", cascade_delete=True)
    results: list["RecognitionResult"] = Relationship(back_populates="student")
    users: list["User"] = Relationship(back_populates="student")


class StudentCreate(StudentBase):
    phone_number: str | None = None
    email: str | None = None


class StudentUpdate(SQLModel):
    name: str | None = None
    group_id: int | None = None
    phone_number: str | None = None
    email: str | None = None


class StudentPublic(StudentBase):
    id: int


class StudentPrivate(StudentBase):
    id: int
    phone_number: str | None
    email: str | None


class StudentPublicWithGroup(StudentPublic):
    group: GroupPublic


class StudentPrivateWithGroup(StudentPrivate):
    group: GroupPublic


class StudentPublicWithGroupAndStream(StudentPublicWithGroup):
    results: "GroupPublicWithStream"


class StudentPublicWithGroupAndReferences(StudentPublicWithGroup):
    references: list["ReferenceFacePublic"]


class StudentPublicWithGroupAndResults(StudentPublicWithGroup):
    results: list["RecognitionResultPublic"]
# </editor-fold>
