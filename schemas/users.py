from typing import TYPE_CHECKING, Optional

from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from .students import Student, Group


# TODO UserBase, UserCreate, UserUpdate, UserPublic

class User(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    user_name: str = Field(index=True)
    hashed_password: str = Field()
    role_id: int | None = Field(foreign_key="role.id", ondelete="SET NULL")
    student_id: int | None = Field(default=None, foreign_key="student.id", ondelete="SET NULL")
    group_id: int | None = Field(default=None, foreign_key="group.id", ondelete="SET NULL")

    role: "Role" = Relationship(back_populates="users")
    student: Optional["Student"] = Relationship(back_populates="user")
    group: Optional["Group"] = Relationship(back_populates="user")


class Role(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    name: str = Field(index=True)

    users: list["User"] = Relationship(back_populates="role", cascade_delete=True)