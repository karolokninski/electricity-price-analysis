FROM python:3.10-slim-buster

COPY requirements.txt .

RUN pip install --upgrade pip && \
    python -m pip install --no-cache-dir -r requirements.txt && \
    pip install gunicorn

COPY api.py /home/app/api.py
COPY weather_data.csv /home/app/weather_data.csv
COPY efficiency_table.csv /home/app/efficiency_table.csv

WORKDIR /home/app

CMD gunicorn api:app -b :80