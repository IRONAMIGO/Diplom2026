# ===========================
# Многоэтапная сборка: builder -> runtime
# ===========================

# --- Этап сборки зависимостей ---
FROM python:3.12-slim AS builder

# Установка системных пакетов, необходимых для сборки зависимостей
# (например, gcc для пакетов с C-расширениями, libgl1 для OpenCV)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libgl1 \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender1 \
    libfontconfig1 \
    && rm -rf /var/lib/apt/lists/*

# Создание виртуального окружения и обновление pip
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
RUN pip install --no-cache-dir --upgrade pip

# Копируем файл с зависимостями и устанавливаем их
COPY requirements.txt .
# RUN pip install --no-cache-dir -r requirements.txt
RUN --mount=type=cache,target=/root/.cache/pip \
    --mount=type=bind,source=requirements.txt,target=requirements.txt \
    python -m pip install -r requirements.txt

# --- Финальный образ ---
FROM python:3.12-slim AS runtime

# Установка только runtime-зависимостей (графические библиотеки для OpenCV/insightface)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender1 \
    libfontconfig1 \
    && rm -rf /var/lib/apt/lists/*

# Копируем виртуальное окружение из builder-а
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Создаём непривилегированного пользователя для безопасности
RUN groupadd -r appuser && useradd -r -g appuser -m -d /home/appuser appuser

# Копируем исходный код приложения
WORKDIR /app
COPY --chown=appuser:appuser . /app

USER appuser

# Переменные окружения по умолчанию (можно переопределить в compose)
ENV HOST=0.0.0.0
ENV PORT=8000

# Для отладки
EXPOSE 8000

# Запуск одного процесса uvicorn (без workers)
CMD ["sh", "-c", "uvicorn main:app --host $HOST --port $PORT"]