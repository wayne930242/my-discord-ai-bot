FROM python:3.13-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

COPY requirements.txt ./
RUN pip install --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

RUN mkdir -p /app/data
VOLUME ["/app/data"]

COPY . .

CMD ["python", "bot.py"]
