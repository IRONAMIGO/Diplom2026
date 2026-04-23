from sqlmodel import create_engine, Session, SQLModel
from .config import DATABASE_URL


engine = create_engine(DATABASE_URL, echo=False, connect_args={"check_same_thread": False})

def init_db():
    """Создать таблицы, если их нет."""
    SQLModel.metadata.create_all(engine)

def get_session():
    with Session(engine) as session:
        yield session