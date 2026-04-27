from typing import TYPE_CHECKING, Optional

from sqlmodel import Field, Relationship, SQLModel
from pydantic import BaseModel

if TYPE_CHECKING:
    from .references import ReferenceFace
    from .students import Student, Group, Stream


# TODO UserBase, UserCreate, UserUpdate, UserPublic

class UserBase(SQLModel):
    user_name: str = Field(index=True)
    role_id: int | None = Field(foreign_key="role.id", ondelete="SET NULL")

class User(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    user_name: str = Field(index=True)
    hashed_password: str = Field()
    role_id: int | None = Field(foreign_key="role.id", ondelete="SET NULL")
    student_id: int | None = Field(default=None, foreign_key="student.id", ondelete="SET NULL")
    group_id: int | None = Field(default=None, foreign_key="group.id", ondelete="SET NULL")
    stream_id: int | None = Field(default=None, foreign_key="stream.id", ondelete="SET NULL")

    role: "Role" = Relationship(back_populates="users")
    student: Optional["Student"] = Relationship(back_populates="user")
    group: Optional["Group"] = Relationship(back_populates="user")
    stream: Optional["Stream"] = Relationship(back_populates="user")

class UserCreate(UserBase):
    password: str
    role_id: int | None = None

class UserUpdate(SQLModel):
    user_name: str | None = None
    password: str | None = None  # для смены пароля
    role_id: int | None = None

class UserPublic(UserBase):
    id: int
    role_id: int | None

class Role(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    name: str = Field(index=True)

    users: list["User"] = Relationship(back_populates="role", cascade_delete=True)

class RolePublic(SQLModel):
    id: int
    name: str