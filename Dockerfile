FROM python:3.13-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

COPY requirements.txt ./
RUN pip install --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

COPY . .
ENV DISCORD_BOT_HOST=0.0.0.0
ENV DISCORD_BOT_PORT=8000

CMD ["python", "bot.py"]
