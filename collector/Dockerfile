FROM python:3.13-slim

WORKDIR /app

COPY pyproject.toml .
RUN pip install --no-cache-dir -e .

COPY . .

ENV PYTHONUNBUFFERED=1
ENV PYTHONFAULTHANDLER=1
ENV PATH="/app/.venv/bin:$PATH"

CMD ["python", "main.py"]