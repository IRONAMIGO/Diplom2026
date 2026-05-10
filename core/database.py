from pwdlib import PasswordHash
from sqlmodel import create_engine, Session, SQLModel, text, select

from core.config import DATABASE_URL, SCOPES
from schemas.users import User, Role            # Необходимо импортировать все модели
from schemas.students import Student, Group     # до SQLModel.metadata.create_all(engine)
from schemas.references import ReferenceFace    # чтобы создались соответствующие таблицы
from schemas.reports import RecognitionData, RecognitionResult


engine = create_engine(DATABASE_URL, echo=False, connect_args={"check_same_thread": False})
password_hash = PasswordHash.recommended()

def init_db():
    """Создать таблицы, если их нет."""
    SQLModel.metadata.create_all(engine)
    if DATABASE_URL.startswith("sqlite"):
        with engine.connect() as connection:
            connection.execute(text("PRAGMA foreign_keys=ON"))  # for SQLite only
    with next(get_session()) as session:
        for name, descript in SCOPES.items():
            curr_role = session.exec(select(Role).where(Role.name == name)).one_or_none()
            if curr_role is None:
                curr_role = Role(name=name, description=descript)
                session.add(curr_role)
                session.commit()
                session.refresh(curr_role)
            curr_user = session.exec(select(User).where(User.user_name == name)).one_or_none()
            if curr_user is None:
                curr_user = User(user_name=name, hashed_password=password_hash.hash(name), role_id=curr_role.id)
                session.add(curr_user)
                session.commit()

def get_session():
    with Session(engine) as session:
        yield session