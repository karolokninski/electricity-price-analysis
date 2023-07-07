import urllib.request
import time
from datetime import date, timedelta, datetime
import os
import pandas as pd

def get_data():
    tomorrow = date.today() + timedelta(1)
    next_day = tomorrow + timedelta(1)

    first_day = tomorrow.strftime('%Y%m%d')
    last_day = next_day.strftime('%Y%m%d')

    # Replace with the actual download link
    download_link = f'https://www.pse.pl/getcsv/-/export/csv/EN_PRICE/data_od/{first_day}/data_do/{last_day}'

    print(f'Downloading from: {download_link}')

    # Download the file
    urllib.request.urlretrieve(download_link, f'new-prices.csv')

    # Wait for the download to complete
    while True:
        time.sleep(1)
        if f'new-prices.csv.crdownload' not in os.listdir():
            break

def create_new_df():
    data_path = 'new-prices.csv'
    dateparse = lambda x: datetime.strptime(x, '%Y%m%d')

    dff = pd.read_csv(data_path, sep=';', index_col=0, parse_dates=['Data'], date_parser=dateparse)

    dff['Time'] = pd.to_numeric(dff['Time'], errors='coerce')
    dff = dff[dff['Time'].notna()]
    dff.RCE = dff.RCE.astype(float)
    dff.Time = dff.Time.astype(int)
    dff.index += dff.Time.apply(lambda x: pd.Timedelta(f'{x-1}h'))
    dff = dff.drop('Time', axis=1)

    return dff

def update_data():
    print("Updating...")
    # get_data()
    print(create_new_df())
    print("Done.")



from sqlalchemy import Column, DateTime, Float, create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
import urllib

Base = declarative_base()

class ElectricityPrices(Base):
    __tablename__ = 'electricity_prices2'

    time = Column('index', DateTime, primary_key=True)
    RCE = Column('RCE', Float)

    def __init__(self, time, RCE):
        self.time = time
        self.RCE = RCE

    def __repr__(self):
        return f'({self.time}) {self.RCE}'
    
conn = 'Driver={ODBC Driver 18 for SQL Server};Server=tcp:electricity-prices.database.windows.net,1433;Database=electricity-prices-db;Uid=kepucino;Pwd=ZAQ!2wsx;Encrypt=yes;TrustServerCertificate=no;Connection Timeout=30;'
params = urllib.parse.quote_plus(conn)
conn_str = 'mssql+pyodbc:///?autocommit=true&odbc_connect={}'.format(params)
engine = create_engine(conn_str, echo=True)

Base.metadata.create_all(bind=engine)

# get_data()
df = create_new_df()

df.to_sql(con=engine, name=ElectricityPrices.__tablename__, if_exists='replace', index=True)

# Session = sessionmaker(bind=engine)
# session = Session()

# results = session.query(ElectricityPrices).all()

# for r in results:
#     print(r)