# Elminster

A Discord bot that uses Gemini and Google ADK to answer questions.

## Requirements

- Python 3.13
- Discord token
- Gemini API key

## Setup

1. Clone the repository
2. Install dependencies
3. Create a `.env` file from `.env.example` and add your API keys

## Running

```bash
python bot.py
```

## Docker

```bash
docker build -t elminster .
```

```bash
docker run -d --env-file .env elminster
```
