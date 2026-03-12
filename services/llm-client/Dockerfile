FROM python:3.11-slim

WORKDIR /app

COPY main.py .

RUN pip install fastapi pydantic uvicorn httpx

EXPOSE 8003

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8003"]
