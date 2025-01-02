FROM python:3.9-slim

RUN apt-get update && apt-get install -y \
    unixodbc-dev \
    gcc \
    g++ \
    && apt-get clean

WORKDIR /app

COPY . /app

RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 7071

CMD ["python", "app.py"]
