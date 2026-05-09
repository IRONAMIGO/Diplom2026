import json
from typing import List, Tuple

import faiss
import numpy as np
from insightface import model_zoo
from ultralytics import YOLO

from core.config import YOLO_MODEL_PATH, ARCFACE_MODEL_PATH, DETECTION_CONFIDENCE_THRESHOLD, DETECTION_IOU_THRESHOLD, \
    FAISS_INDEX_PATH, FAISS_ID_MAP_PATH, RECOGNITION_THRESHOLD
from core.database import get_session
from core.image_utils import crop_face, read_image_file
from schemas.reports import RecognitionResultCreate, RecognitionData


class FaceRecognitionPipeline:
    def __init__(self):
        self.detector = FaceDetector()
        self.embedder = FaceEmbedder()
        self.index = FaissIndex()
        self.index.load()  # загружаем сохранённый индекс

    def recognize_group_image(self, data_id: int, image: np.ndarray = None, scale=1.0) -> List[RecognitionResultCreate]:
        """
        Обрабатывает групповое фото, распознаёт лица.
        Возвращает список объектов RecognitionResult.
        """
        if image is None:
            with next(get_session()) as session:
                data = session.get(RecognitionData, data_id)
                image =  read_image_file(data.image_path)
        boxes = self.detector.detect(image)

        results = []
        for (x1, y1, x2, y2, det_conf) in boxes:
            face_crop = crop_face(image, (x1, y1, x2, y2))
            emb = self.embedder.extract(face_crop)

            # Поиск ближайшего соседа
            distances, indices = self.index.search(emb, k=1)
            reference_db_id = None
            similarity = None
            if len(distances) > 0 and distances[0] >= RECOGNITION_THRESHOLD:
                # distances для IP = cosine similarity
                similarity = float(distances[0])
                # Получить reference_id по индексу faiss (который является database_id)
                reference_db_id = self.index.index_to_id.get(int(indices[0]))

            result = RecognitionResultCreate(
                data_id=data_id,
                reference_db_id=reference_db_id,
                bbox_x1=x1*scale,
                bbox_y1=y1*scale,
                bbox_x2=x2*scale,
                bbox_y2=y2*scale,
                confidence=det_conf,
                similarity=similarity
            )
            results.append(result)

        return results


class FaceDetector:
    def __init__(self):
        self.model = YOLO(YOLO_MODEL_PATH)

    def detect(self, image: np.ndarray) -> List[Tuple[float, float, float, float, float]]:
        results = self.model(
            image,
            conf=DETECTION_CONFIDENCE_THRESHOLD,
            iou=DETECTION_IOU_THRESHOLD,
            verbose=False
        )
        boxes = []
        if results and results[0].boxes:
            for box in results[0].boxes:
                x1, y1, x2, y2 = box.xyxy[0].tolist()
                conf = float(box.conf[0])
                boxes.append((x1, y1, x2, y2, conf))
        return boxes


class FaceEmbedder:
    def __init__(self):
        self.model: model_zoo.ArcFaceONNX = model_zoo.get_model(str(ARCFACE_MODEL_PATH), providers=['CPUExecutionProvider'])
        self.model.prepare(ctx_id=-1)  # -1 для CPU, 0 для GPU если доступен

    def extract(self, face_crop: np.ndarray) -> np.ndarray:
        if face_crop.size == 0:
            raise ValueError("Пустой face_crop передан в embedder")

        embedding = self.model.get_feat(face_crop)

        # Нормализация (L2)
        norm = np.linalg.norm(embedding)
        if norm > 0:
            embedding = embedding / norm
        return embedding.astype(np.float32)


class FaissIndex:
    def __init__(self, dimension: int = 512):
        self.dimension = dimension
        # Используем индекс с L2-нормированными векторами -> фактически косинусное расстояние
        self.index = faiss.IndexFlatIP(dimension)
        self.id_to_index = {}   # mapping: database_id -> позиция в Faiss
        self.index_to_id = {}   # mapping: позиция -> database_id
        self.next_position = 0
        self.index_path = FAISS_INDEX_PATH
        self.id_map_path = FAISS_ID_MAP_PATH

    def add(self, db_id: int, embedding: np.ndarray) -> None:
        if db_id in self.id_to_index:
            # Обновление существующего? В данной реализации удалим и добавим заново
            self.remove(db_id)
        pos = self.next_position
        self.index.add(embedding.reshape(1, -1))
        self.id_to_index[db_id] = pos
        self.index_to_id[pos] = db_id
        self.next_position += 1

    def remove(self, id_from_db: int) -> None:
        # Faiss не поддерживает удаление напрямую в простом индексе.
        # Перестроим индекс.
        keep_ids = [db_id for db_id in self.id_to_index.keys() if db_id != id_from_db]
        if not keep_ids:
            self.index.reset()
            self.id_to_index.clear()
            self.index_to_id.clear()
            self.next_position = 0
            return

        # Соберём сохраняемые эмбеддинги
        embeddings = []
        new_id_to_index = {}
        new_index_to_id = {}
        for new_pos, db_id in enumerate(keep_ids):
            old_pos = self.id_to_index[db_id]
            emb = self.index.reconstruct(old_pos)
            embeddings.append(emb)
            new_id_to_index[db_id] = new_pos
            new_index_to_id[new_pos] = db_id

        # Пересоздаём индекс
        self.index = faiss.IndexFlatIP(self.dimension)
        if embeddings:
            self.index.add(np.vstack(embeddings))
        self.id_to_index = new_id_to_index
        self.index_to_id = new_index_to_id
        self.next_position = len(keep_ids)

    def search(self, embedding: np.ndarray, k: int = 1) -> Tuple[np.ndarray, np.ndarray]:
        if self.index.ntotal == 0:
            return np.array([]), np.array([])
        embedding = embedding / np.linalg.norm(embedding)
        distances, indices = self.index.search(embedding.reshape(1, -1), k)
        return distances[0], indices[0]

    def save(self, path: str) -> None:
        faiss.write_index(self.index, path)
        # Сохраняем маппинги
        map_data = {
            "id_to_index": self.id_to_index,
            "index_to_id": self.index_to_id,
            "next_position": self.next_position
        }
        with open(self.id_map_path, "w") as f:
            json.dump(map_data, f)

    def load(self) -> None:
        if self.index_path.exists():
            self.index = faiss.read_index(str(self.index_path))
            with open(self.id_map_path, "r") as f:
                map_data = json.load(f)
            self.id_to_index = {int(k): v for k, v in map_data["id_to_index"].items()}
            self.index_to_id = {int(k): int(v) for k, v in map_data["index_to_id"].items()}
            self.next_position = map_data["next_position"]
