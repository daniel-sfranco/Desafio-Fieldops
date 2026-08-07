FROM python:3.11-slim

COPY requirements.txt .

RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

COPY . .

ENV PYTHONPATH=/app/src

CMD [ "fastapi", "dev", "src/main.py", "--host", "0.0.0.0", "--port", "8000" ]