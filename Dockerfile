FROM python:3.10-slim

RUN apt-get update && \
    apt-get install -y wget unzip curl gnupg chromium chromium-driver && \
    pip install --upgrade pip

WORKDIR /app
COPY . .

RUN pip install -r requirements.txt

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
