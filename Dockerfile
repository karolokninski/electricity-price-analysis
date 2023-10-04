FROM python:3.10-slim-buster

COPY requirements.txt .

RUN pip install --upgrade pip && \
    python -m pip install --no-cache-dir -r requirements.txt && \
    pip install gunicorn

RUN apt-get update && \
    apt-get install -y curl gnupg && \
    sh -c "curl https://packages.microsoft.com/keys/microsoft.asc | apt-key add -" && \ 
    apt-get update && \
    sh -c "curl https://packages.microsoft.com/config/ubuntu/20.04/prod.list > /etc/apt/sources.list.d/mssql-release.list" && \
    apt-get update && \
    ACCEPT_EULA=Y apt-get install -y msodbcsql18 && \
    ACCEPT_EULA=Y apt-get install -y mssql-tools18

COPY api.py /home/app/api.py
COPY weather_data.csv /home/app/weather_data.csv
COPY efficiency_table.csv /home/app/efficiency_table.csv

WORKDIR /home/app

CMD gunicorn api:app -b :80