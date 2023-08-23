from flask import Flask, request, jsonify, abort
from flask_cors import CORS
import pandas as pd
import requests
import json
import os

from sqlalchemy import Column, DateTime, Float, String, Integer, create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
import urllib

API_KEY = os.environ['API_SECRET']
WEATHER_API_KEY = os.environ['WEATHER_API_SECRET']
AZURE_DB_PWD = os.environ['AZURE_DB_PWD']

Base = declarative_base()

class ElectricityPrices(Base):
    __tablename__ = 'electricity_prices'

    index = Column('index', DateTime, primary_key=True, unique=True)
    RCE = Column('RCE', Float, unique=True)

    def __init__(self, index, RCE):
        self.index = index
        self.RCE = RCE

    def __repr__(self):
        return f'({self.index}) {self.RCE}'

class Emails(Base):
    __tablename__ = 'emails'

    email = Column(String(255), primary_key=True, unique=True)

    def __init__(self, email):
        self.email = email

    def __repr__(self):
        return f'{self.email}'

driver = '{ODBC Driver 18 for SQL Server}'
uid = 'kepucino'
pwd = AZURE_DB_PWD

conn = f'Driver={driver};Server=tcp:electricity-prices.database.windows.net,1433;Database=electricity-prices-db;Uid={uid};Pwd={pwd};Encrypt=yes;TrustServerCertificate=no;Connection Timeout=30;'
params = urllib.parse.quote_plus(conn)
conn_str = 'mssql+pyodbc:///?autocommit=true&odbc_connect={}'.format(params)

engine = create_engine(conn_str, echo=True)
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)

app = Flask(__name__)
cors = CORS(app, resources={r"/api/*": {"origins": "*"}})

def require_token(func, *args, **kwargs):
    def wrapper():
        if 'Authorization' in request.headers and request.headers['Authorization'] == f'Bearer {API_KEY}':
            return func(*args, **kwargs)

        else:
            abort(401, description="Error message you want the reader to receive.")
        
    wrapper.__name__ = func.__name__

    return wrapper

@app.route('/api/estimate', methods=['POST'])
@require_token
def estimate():
    request_data = request.json

    from_csv = 1

    if from_csv:
        weather_df = pd.read_csv('weather_data.csv', index_col='time', parse_dates=True)

    else:
        r = requests.get('https://api.oikolab.com/weather',
                        params={'param': ['surface_solar_radiation'],
                                'start': request_data['start'],
                                'end': request_data['end'],
                                'lat': request_data['lat'],
                                'lon': request_data['lon'],
                                'api-key': WEATHER_API_KEY}
        )

        weather_data = json.loads(r.json()['data'])
        weather_df = pd.DataFrame(index=pd.to_datetime(weather_data['index'], unit='s'),
                                data=weather_data['data'],
                                columns=weather_data['columns']
        )

        # weather_df.to_csv('weather_data.csv')

    weather_df.index += pd.Timedelta(hours=2) # convert from UTC to UTC+2
                                            # mozliwe, ze trzeba bedzie sczytywac strefe czasowa z koordynatow (lat, long)
    weather_df = weather_df[request_data['start']:request_data['end']]

    eff_table = pd.read_csv('efficiency_table.csv', index_col='angle')

    Wp = request_data['peak_power']
    eff = eff_table[str(request_data['azimuth'])].loc[request_data['angle']]
    radiation = weather_df['surface_solar_radiation (W/m^2)']

    my_query = 'SELECT * FROM [dbo].[electricity_prices]'
    electricity_prices_df = pd.read_sql(my_query, engine, index_col='index')
    electricity_prices_df = electricity_prices_df.sort_index()
    electricity_prices_df = electricity_prices_df[request_data['start']:request_data['end']]

    production_df = pd.DataFrame()
    production_df['production'] = (Wp * eff * radiation / 1000).values
    production_df['time'] = radiation.index
    production_df.set_index('time', inplace=True)

    profit_df = pd.DataFrame()
    profit_df['profit'] = (production_df['production'] * electricity_prices_df.RCE / 1000000).values
    profit_df['time'] = production_df.index
    profit_df.set_index('time', inplace=True)

    response_df = pd.merge(profit_df, production_df, on='time', how='outer')
    response_df = response_df.dropna()

    response = {
        'time': response_df.index.strftime("%Y-%m-%d %H:%M:%S").tolist(),
        'production': response_df['production'].values.tolist(),
        'profit': response_df['profit'].values.tolist()
    }

    return jsonify(response)

@app.route('/api/save_email', methods=['POST'])
@require_token
def save_email():
    request_data = request.json

    session = Session()

    if isinstance(request_data['email'], str):
        new_email = Emails(email=request_data['email'])

        existing_data_point = session.query(Emails).filter_by(email=request_data['email']).first()

        if existing_data_point is None:
            session.add(new_email)

    else:
        for email in request_data['email']:
            new_email = Emails(email=email)

            existing_data_point = session.query(Emails).filter_by(email=email).first()

            if existing_data_point is None:
                session.add(new_email)

    try:
        session.commit()
        response = {'status': 200}

    except Exception as e:
        session.rollback()
        response = {'status': 500}

    session.close()

    return jsonify(response)

if __name__ == '__main__':
    app.run()
