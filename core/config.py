import os
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent

# Путь сохранения эталонных фото
PHOTO_DIR = Path(os.getenv("PHOTO_DIR", BASE_DIR / "data/photo"))
# Путь сохранения эталонных фото
REPORT_DIR = Path(os.getenv("PHOTO_DIR", BASE_DIR / "data/reports"))

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