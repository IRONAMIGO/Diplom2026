from sqlmodel import create_engine, Session, SQLModel
from .config import DATABASE_URL
from schemas.users import User, Role            # Необходимо импортировать все модели
from schemas.students import Student, Group     # до SQLModel.metadata.create_all(engine)
from schemas.references import ReferenceFace    # чтобы создались соответствующие таблицы


engine = create_engine(DATABASE_URL, echo=False, connect_args={"check_same_thread": False})

def init_db():
    """Создать таблицы, если их нет."""
    SQLModel.metadata.create_all(engine)

def get_session():
    with Session(engine) as session:
        yield session