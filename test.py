import os
import pathlib
import uuid

import cv2
from sqlmodel import select

from core.config import REPORT_DIR, PHOTO_DIR, PHOTO_MAX_SIZE, REPORT_MAX_SIZE, FAISS_INDEX_PATH, BASE_DIR
from core.database import init_db, get_session
from core.image_utils import crop_face, reduce_image, write_image
from core.pipeline import FaceRecognitionPipeline
from schemas.references import ReferenceFace
from schemas.students import Stream, Group, Student

if __name__ == '__main__':
    print("PHOTO_DIR = ", PHOTO_DIR)

    # Инициализация БД
    init_db()
    # Создание записей потока и группы
    with next(get_session()) as session:
        curr_group = session.exec(select(Group).where(Group.name == "Тестовая группа")).first()
        if curr_group is None:
            db_stream = Stream(name="Тестовый поток")
            curr_group = Group(name="Тестовая группа", stream=db_stream)
            session.add(curr_group)
            session.commit()
            session.refresh(curr_group)
    # Инициализация пайплайна
    pipeline = FaceRecognitionPipeline()
    print("Пайплайн загружен...")

    # Получаем список директорий эталонных фото
    dir_list = ['../test/' + dir_name for dir_name in os.listdir('../test') if os.path.isdir('../test/' + dir_name)]
    # Загружаем эталонные фото
    for dir_name in dir_list:
        student_name = pathlib.Path(dir_name).stem
        with next(get_session()) as session:
            curr_student = session.exec(select(Student).where(Student.name == student_name)).first()
            if curr_student is None:
                curr_student = Student(name=student_name, group_id=curr_group.id)
                session.add(curr_student)
                session.commit()
                session.refresh(curr_student)
        ref_img_list = [dir_name + '/' + img_name
                        for img_name in os.listdir(dir_name)
                        if pathlib.PurePath(img_name).suffix.lower() in ['.jpg', '.jpeg', '.png']]
        for img_name in ref_img_list:
            file_name = f"{uuid.uuid4()}{pathlib.PurePath(img_name).suffix.lower()}"
            file_path = PHOTO_DIR / file_name
            # Убедимся, что директория для фото существует
            PHOTO_DIR.mkdir(parents=True, exist_ok=True)
            # Относительный путь от BASE_DIR (для хранения в БД)
            file_db_path = "/" + str(file_path.relative_to(BASE_DIR)).replace("\\","/")
            # Загружаем изображение
            img = cv2.imread(img_name)
            # Детектируем лица
            boxes = pipeline.detector.detect(img)
            if not boxes:
                raise ValueError("На изображении не найдено лицо")
            # Берём бокс с максимальной уверенностью
            best_box = max(boxes, key=lambda b: b[4])
            x1, y1, x2, y2, _ = best_box
            # Кроп
            face_crop = crop_face(img, (x1, y1, x2, y2))
            # Извлекаем эмбеддинг
            embedding = pipeline.embedder.extract(face_crop)
            # Уменьшение размеров изображения (после извлечения всех необходимых данных)
            img_small, _ = reduce_image(img, PHOTO_MAX_SIZE)
            # Сохраняем изображение на диске
            write_image(file_path, img_small)
            # Создаём запись в БД
            with next(get_session()) as session:
                db_reference = ReferenceFace(student_id=curr_student.id, embedding=embedding, image_path=str(file_db_path))
                session.add(db_reference)
                session.commit()
                session.refresh(db_reference)
            # Добавляем в Faiss индекс
            pipeline.index.add(db_reference.id, embedding)
            pipeline.index.save(str(FAISS_INDEX_PATH))
            print(f"Эталонное фото {img_name} загружено...")

    # Получаем список фото для распознавания
    img_list = ['../test/' + img_name
                for img_name in os.listdir('../test/')
                if pathlib.PurePath(img_name).suffix.lower() in ['.jpg', '.jpeg', '.png']]
    for img_name in img_list:
        file_name = f"{uuid.uuid4()}{pathlib.PurePath(img_name).suffix.lower()}"
        file_path = REPORT_DIR / file_name
        # Убедимся, что директория существует
        REPORT_DIR.mkdir(parents=True, exist_ok=True)
        # Загружаем изображение
        img = cv2.imread(img_name)
        # Уменьшенное изображение для сохранения
        img_small, scale = reduce_image(img, REPORT_MAX_SIZE)
        # Определяем присутствующих на фото
        results = pipeline.recognize_group_image(1, img, scale)
        if not results:
            raise ValueError("На изображении не найдено лиц")
        bboxes_with_names = []
        for result in results:
            student_id = None
            student_name = "Неизвестный"
            if result.reference_db_id is not None:
                with next(get_session()) as session:
                    ref = session.get(ReferenceFace, result.reference_db_id)
                    if ref:
                        student_id = ref.student_id
                        student_name = ref.student.name
            # --- Отрисовка на изображении ---
            x1, y1, x2, y2 = (int(result.bbox_x1),
                              int(result.bbox_y1),
                              int(result.bbox_x2),
                              int(result.bbox_y2))  # Преобразуем координаты в int
            color = (0, 255, 0) if student_id is not None else (0, 0, 255)  # Зелёный — есть ID, красный — неизвестно
            cv2.rectangle(img_small, (x1, y1), (x2, y2), color, 1)
            font_scale = 0.5
            font_thickness = 1
            cv2.putText(
                img_small,
                student_name,
                (x1, y1 - 10),
                cv2.FONT_HERSHEY_COMPLEX,
                font_scale,
                color,
                font_thickness
            )
        print(f"Фото {img_name} обработано...")
        cv2.imwrite(file_path, img_small)
