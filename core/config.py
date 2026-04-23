import os
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent

# База данных
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{BASE_DIR / 'data/app.db'}")


TEST_VAR = os.getenv("TEST_VAR", "1111")