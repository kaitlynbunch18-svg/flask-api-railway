FROM python:3.11-slim

WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

COPY . .

ENV FLASK_APP=app
CMD ["gunicorn", "app:app", "--bind", "0.0.0.0:8080", "--workers", "2", "--threads", "4"]
