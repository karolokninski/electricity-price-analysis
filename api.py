from flask import Flask, request, jsonify, abort
from flask_cors import CORS
import pandas as pd
import requests
import json
import os

from sqlalchemy import Column, DateTime, Float, String, Integer, create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
import urllib
import datetime

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication

API_KEY = os.environ['API_SECRET']
WEATHER_API_KEY = os.environ['WEATHER_API_SECRET']
AZURE_DB_PWD = os.environ['AZURE_DB_PWD']
EMAIL_PWD = os.environ['EMAIL_PWD']

Base = declarative_base()

class ElectricityPrices(Base):
    __tablename__ = 'electricity_prices'

    index = Column('index', DateTime, primary_key=True, unique=True)
    RCE = Column('RCE', Float)

    def __init__(self, index, RCE):
        self.index = index
        self.RCE = RCE

    def __repr__(self):
        return f'({self.index}) {self.RCE}'

class Emails(Base):
    __tablename__ = 'emails'

    email = Column(String(255), primary_key=True, unique=True)
    time_stamp = Column(DateTime, default=datetime.datetime.utcnow)

    def __init__(self, email):
        self.email = email
        self.time_stamp = datetime.datetime.utcnow()

    def __repr__(self):
        return f"Email(email='{self.email}', time_stamp='{self.time_stamp}')"


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

def temp_fraction(temp):
    if (temp > 15):
        return 0

    return -0.0181818181818 * temp + 0.272727272727

@app.route('/api/estimate', methods=['POST'])
@require_token
def estimate():
    request_data = request.json

    print(request_data)

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

    weather_df.index += pd.Timedelta(hours=2)

    weather_df = weather_df[request_data['start']:request_data['end']]

    eff_table = pd.read_csv('efficiency_table.csv', index_col='angle')

    Wp = request_data['peak_power']
    eff = eff_table[str(request_data['azimuth'])].loc[request_data['angle']]
    radiation = weather_df['surface_solar_radiation (W/m^2)']

    my_query = 'SELECT * FROM [dbo].[electricity_prices]'
    electricity_prices_df = pd.read_sql(my_query, engine, index_col='index')
    electricity_prices_df = electricity_prices_df.sort_index()
    electricity_prices_df = electricity_prices_df[request_data['start']:request_data['end']]
    
    nominal_power_sum = 0

    if request_data['heating']:
        for device in request_data['heating']:
            nominal_power = float(device[0])

            if len(device) == 2: # heat pump
                nominal_power /= float(device[1])

            nominal_power_sum += nominal_power

    response_df = pd.DataFrame(index = pd.Index(radiation.index).union(pd.Index(electricity_prices_df.index)))
    response_df['production'] = Wp * eff * radiation / 1000
    response_df['profit'] = response_df['production'] * electricity_prices_df.RCE / 1000000
    # response_df['consumption'] = weather_df['temperature (degC)'].apply(temp_fraction)
    # response_df['consumption'] *= nominal_power_sum
    response_df['consumption'] = -0.0181818181818 * weather_df['temperature (degC)'] + 0.272727272727 # fraction of temperature
    response_df.loc[weather_df['temperature (degC)'] > 15, 'consumption'] = 0
    response_df = response_df.dropna()

    response = {
        'time': response_df.index.strftime("%Y-%m-%d %H:%M:%S").tolist(),
        'production': response_df['production'].values.tolist(),
        'profit': response_df['profit'].values.tolist(),
        'consumption': response_df['consumption'].values.tolist()
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

    # Send email
    email_address = "raport@net-billing.online"
    email_password = EMAIL_PWD
    recipient_email = request_data['email']

    # Create the message you want to send
    subject = "Your Email Subject"
    body = "Hello " + recipient_email

    msg = MIMEMultipart()
    msg['From'] = email_address
    msg['To'] = recipient_email
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain'))

    # Attach a file (replace 'file.txt' with the actual file path)
    file_path = 'file.txt'
    with open(file_path, 'rb') as attachment:
        part = MIMEApplication(attachment.read(), Name='file.txt')

    part['Content-Disposition'] = f'attachment; filename="{file_path}"'
    msg.attach(part)

    # OVH.net SMTP server details
    smtp_server = "ssl0.ovh.net"
    smtp_port = 465

    try:
        server = smtplib.SMTP_SSL(smtp_server, smtp_port)
        server.login(email_address, email_password)
        server.sendmail(email_address, recipient_email, msg.as_string())
        server.quit()
        print("Email sent successfully")

    except Exception as e:
        print(f"Email sending failed: {str(e)}")

    return jsonify(response)

if __name__ == '__main__':
    app.run()
