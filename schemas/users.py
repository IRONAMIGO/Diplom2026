from typing import TYPE_CHECKING, Optional

from pydantic import BaseModel
from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from .students import Student, Group, Stream


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: str | None = None


class UserBase(SQLModel):
    user_name: str = Field(index=True)
    role_id: int | None = Field(foreign_key="role.id", ondelete="SET NULL")
    student_id: int | None = Field(default=None, foreign_key="student.id", ondelete="SET NULL")
    group_id: int | None = Field(default=None, foreign_key="group.id", ondelete="SET NULL")
    stream_id: int | None = Field(default=None, foreign_key="stream.id", ondelete="SET NULL")


class User(UserBase, table=True):
    id: int | None = Field(default=None, primary_key=True)
    hashed_password: str = Field()

    role: "Role" = Relationship(back_populates="users")
    student: Optional["Student"] = Relationship(back_populates="users")
    group: Optional["Group"] = Relationship(back_populates="users")
    stream: Optional["Stream"] = Relationship(back_populates="users")


class UserCreate(UserBase):
    password: str


class UserUpdate(SQLModel):
    user_name: str | None = None
    password: str | None = None  # для смены пароля
    role_id: int | None = None
    student_id: int | None = None
    group_id: int | None = None
    stream_id: int | None = None


class UserPublic(UserBase):
    id: int


class UserPublicWithRole(UserPublic):
    role: "Role"


class RoleBase(SQLModel):
    name: str = Field(index=True)
    description: str = Field()


class Role(RoleBase, table=True):
    id: int | None = Field(default=None, primary_key=True)

    users: list["User"] = Relationship(back_populates="role", cascade_delete=True)


class RoleCreate(RoleBase):
    pass


class RoleUpdate(SQLModel):
    name: str | None = None
    description: str | None = None


class RolePublic(RoleBase):
    id: int
