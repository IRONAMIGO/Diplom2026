from pathlib import Path

import cv2
import numpy as np


def read_image_file(path: Path) -> np.ndarray:
    """Чтение изображения в BGR (OpenCV)."""
    img = cv2.imread(path)
    if img is None:
        raise FileNotFoundError(f"Не удалось прочитать изображение: {path}")
    return img


def read_image_bytes(img_bytes:  bytes) -> np.ndarray:
    """Чтение изображения в BGR (OpenCV)."""
    np_arr = np.frombuffer(img_bytes, np.uint8)
    img = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
    if img is None:
        raise ValueError("Не удалось декодировать изображение из байтов")
    return img


def reduce_image(image: np.ndarray, limit: int) -> tuple[np.ndarray, float]:
    """Уменьшает изображение с сохранением пропорций так, чтобы ширина и высота не превышали limit."""

    h, w = image.shape[:2]
    if h <= limit and w <= limit:
        return image, 1
    # Коэффициент масштабирования, чтобы большая сторона стала равна limit
    scale = limit / max(h, w)
    # Вычисляем новые размеры с округлением до ближайшего целого
    new_h = int(round(h * scale))
    new_w = int(round(w * scale))
    # Уменьшаем изображение с помощью интерполяции INTER_AREA (оптимально для уменьшения)
    resized = cv2.resize(image, (new_w, new_h), interpolation=cv2.INTER_AREA)
    return resized, scale


def write_image(path: Path, image: np.ndarray) -> None:
    """Сохранение изображения."""
    path.parent.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(path, image)


def crop_face(image: np.ndarray, bbox: tuple[float, float, float, float]) -> np.ndarray:
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
