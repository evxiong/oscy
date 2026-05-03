# syntax=docker/dockerfile:1

FROM python:3.12-slim

# Prevents Python from writing pyc files.
ENV PYTHONDONTWRITEBYTECODE=1

# Keeps Python from buffering stdout and stderr to avoid situations where the
# application crashes without emitting any logs due to buffering.
ENV PYTHONUNBUFFERED=1

WORKDIR /app

RUN adduser --system --uid 1001 --group appuser

# Download dependencies as a separate step to take advantage of Docker's
# caching. Leverage a cache mount to /root/.cache/pip to speed up subsequent
# builds. Leverage a bind mount to requirements.txt to avoid having to copy them
# into into this layer.
RUN --mount=type=cache,target=/root/.cache/pip \
    --mount=type=bind,source=requirements.txt,target=requirements.txt \
    python -m pip install -r requirements.txt

USER appuser

COPY ./api /app/api

EXPOSE 8000

CMD ["fastapi", "run", "api/main.py"]
