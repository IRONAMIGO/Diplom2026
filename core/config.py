import os
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent

# CORS URL фронтэнда
CORS_URL = os.getenv("CORS_URL", "http://localhost:5173")

# Путь сохранения эталонных фото
PHOTO_DIR = Path(os.getenv("PHOTO_DIR", BASE_DIR / "data/photo"))
# Максимальный размер эталонных фото
PHOTO_MAX_SIZE = 300
# Путь сохранения распознанных фото
REPORT_DIR = Path(os.getenv("REPORT_DIR", BASE_DIR / "data/reports"))
# Максимальный размер распознанных фото
REPORT_MAX_SIZE = 800

# База данных
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{BASE_DIR / 'data/app.db'}")

# Пути к моделям
YOLO_MODEL_PATH = Path(os.getenv("YOLO_MODEL_PATH", BASE_DIR / "models/face_model_yolov11s_100_epoch.pt"))
ARCFACE_MODEL_PATH = Path(os.getenv("ARCFACE_MODEL_PATH", BASE_DIR / "models/w600k_r50.onnx"))

# Параметры детекции
DETECTION_CONFIDENCE_THRESHOLD = float(os.getenv("DETECTION_CONFIDENCE_THRESHOLD", "0.5"))
DETECTION_IOU_THRESHOLD = float(os.getenv("DETECTION_IOU_THRESHOLD", "0.45"))

# Faiss индекс
FAISS_INDEX_PATH = Path(os.getenv("FAISS_INDEX_PATH", BASE_DIR / "data/faiss_index.bin"))
FAISS_ID_MAP_PATH = Path(os.getenv("FAISS_ID_MAP_PATH", BASE_DIR / "data/faiss_id_map.json"))

# Параметры распознавания
RECOGNITION_THRESHOLD = float(os.getenv("RECOGNITION_THRESHOLD", "0.6"))

# Хэширование
SECRET_KEY = "eb0ea17d9e0aa17b07f21ca219c17d204445f2bc33a7f8c8949d0745b81eab54"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 1500

# Определяем доступные scope
SCOPES = {
    "admin": "Полный доступ к системе",
    "teacher": "Доступ преподавателя (управление эталонами, отчётами)",
    "student": "Доступ студента (просмотр своих данных)",
}