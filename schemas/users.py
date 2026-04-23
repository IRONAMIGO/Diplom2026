from sqlmodel import Field, Relationship, SQLModel


# TODO UserBase, UserCreate, UserUpdate, UserPublic

class User(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    user_name: str = Field(index=True)
    hashed_password: str = Field()
    role_id: int | None = Field(foreign_key="role.id", ondelete="SET NULL")

    role: "Role" = Relationship(back_populates="users")


class Role(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    name: str = Field(index=True)

    users: list["User"] = Relationship(back_populates="role", cascade_delete=True)