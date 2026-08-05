FROM python:3.11-slim

COPY requirements.txt .

RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

COPY . .

RUN chmod +x src/main.py

CMD [ "fastapi", "run", "src/main.py" ]