import datetime
import logging
import azure.functions as func
import urllib.request
from datetime import date, timedelta, datetime, timezone
import os
import pandas as pd
from sqlalchemy import Column, DateTime, Float, create_engine
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import sessionmaker
import urllib

AZURE_DB_PWD = os.environ['AZURE_DB_PWD']

Base = declarative_base()

class ElectricityPrices(Base):
    __tablename__ = 'electricity_prices'

    time = Column('index', DateTime, primary_key=True, unique=True, index=True)
    RCE = Column('RCE', Float)

    def __init__(self, time, RCE):
        self.time = time
        self.RCE = RCE

    def __repr__(self):
        return f'({self.time}) {self.RCE}'
    
driver = '{ODBC Driver 17 for SQL Server}'
uid = 'kepucino'
pwd = AZURE_DB_PWD

conn = f'Driver={driver};Server=tcp:electricity-prices.database.windows.net,1433;Database=electricity-prices-db;Uid={uid};Pwd={pwd};Encrypt=yes;TrustServerCertificate=no;Connection Timeout=30;'
params = urllib.parse.quote_plus(conn)
conn_str = 'mssql+pyodbc:///?autocommit=true&odbc_connect={}'.format(params)
engine = create_engine(conn_str, echo=True)

Base.metadata.create_all(bind=engine)
Session = sessionmaker(bind=engine)

def update_db():
    start = date.today()
    end = start + timedelta(1)

    first_day = start.strftime('%Y%m%d')
    last_day = end.strftime('%Y%m%d')

    # Replace with the actual download link
    download_link = f'https://www.pse.pl/getcsv/-/export/csv/EN_PRICE/data_od/{first_day}/data_do/{last_day}'

    dateparse = lambda x: datetime.strptime(x, '%Y%m%d')

    downloaded_data_df = pd.read_csv(download_link, sep=';', index_col=0, parse_dates=['Data'], date_parser=dateparse)

    downloaded_data_df['Time'] = pd.to_numeric(downloaded_data_df['Time'], errors='coerce')
    downloaded_data_df = downloaded_data_df[downloaded_data_df['Time'].notna()]
    downloaded_data_df.RCE = downloaded_data_df.RCE.astype(float)
    downloaded_data_df.Time = downloaded_data_df.Time.astype(int)
    downloaded_data_df.index += downloaded_data_df.Time.apply(lambda x: pd.Timedelta(f'{x-1}h'))
    downloaded_data_df = downloaded_data_df.drop('Time', axis=1)

    # downloaded_data_df.to_sql(con=engine, name=ElectricityPrices.__tablename__, if_exists='append', index=True)

    session = Session()

    for index, row in downloaded_data_df.iterrows():
        new_data_point = ElectricityPrices(time=index, RCE=row.RCE)

        existing_data_point = session.query(ElectricityPrices).filter_by(time=index).first()

        if existing_data_point is None:
            session.add(new_data_point)

    session.commit()
    session.close()

def main(mytimer: func.TimerRequest) -> None:
    utc_timestamp = datetime.utcnow().replace(tzinfo=timezone.utc).isoformat()

    if mytimer.past_due:
        logging.info('The timer is past due!')

    update_db()

    logging.info('Python timer trigger function ran at %s', utc_timestamp)