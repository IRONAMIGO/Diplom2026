from pathlib import Path
from typing import Tuple

import cv2
import numpy as np


def read_image(path: Path) -> np.ndarray:
    """Чтение изображения в BGR (OpenCV)."""
    img = cv2.imread(str(path))
    if img is None:
        raise FileNotFoundError(f"Не удалось прочитать изображение: {path}")
    return img


def write_image(path: Path, image: np.ndarray) -> None:
    """Сохранение изображения."""
    path.parent.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(path), image)


def crop_face(image: np.ndarray, bbox: Tuple[float, float, float, float]) -> np.ndarray:
    """Вырезать область лица."""
    x1, y1, x2, y2 = [int(v) for v in bbox]
    h, w = image.shape[:2]
    x1 = max(0, x1)
    y1 = max(0, y1)
    x2 = min(w, x2)
    y2 = min(h, y2)

    if x1 >= x2 or y1 >= y2:
        raise ValueError(f"Некорректный bbox: {x1, y1, x2, y2}")

    cropped = image[y1:y2, x1:x2]
    if cropped.size == 0:
        raise ValueError("Пустой кроп лица")
    return cropped
