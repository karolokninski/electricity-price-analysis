FROM python:3.10-slim-buster

COPY requirements.txt .

RUN pip install --upgrade pip && \
    python -m pip install --no-cache-dir -r requirements.txt && \
    pip install gunicorn

COPY app.py /home/app/app.py
COPY prices.csv /home/app/prices.csv
COPY assets /home/app/assets

WORKDIR /home/app

CMD gunicorn app:server -b :80