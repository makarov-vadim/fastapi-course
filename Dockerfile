# syntax=docker/dockerfile:1

# --- Этап сборки (Builder) ---
FROM python:3.13-slim-bookworm AS builder

# Устанавливаем uv из официального образа (быстро и без лишних слоев)
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

# Важные настройки для Docker:
# UV_COMPILE_BYTECODE=1 — ускоряет запуск контейнера
# UV_LINK_MODE=copy — необходимо для копирования venv между этапами
ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=never

# 1. Сначала копируем только файлы зависимостей (для кэширования слоев)
COPY pyproject.toml uv.lock ./

# 2. Устанавливаем зависимости (без самого проекта)
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-install-project

# 3. Копируем код и устанавливаем проект
COPY . .
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen


# --- Этап запуска (Runtime) ---
FROM python:3.13-slim-bookworm AS runtime

# Создаем非-root пользователя для безопасности
RUN useradd --create-home --uid 1000 appuser

WORKDIR /app

# Копируем виртуальное окружение и код из builder
COPY --from=builder --chown=appuser:appuser /app/.venv /app/.venv
COPY --from=builder --chown=appuser:appuser /app /app

# Активируем venv через PATH
ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONUNBUFFERED=1

USER appuser

# Указываем порт (для документации)
EXPOSE 8000

# Команда запуска (замените main:app на ваш модуль)
CMD ["uvicorn", "src.app.main:app", "--host", "0.0.0.0", "--port", "8000"]