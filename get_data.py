from flask import Flask, request, jsonify
import pandas as pd
import requests
import json

app = Flask(__name__)

@app.route('/estimate', methods=['POST'])
def estimate():
    request_data = request.json

    from_csv = 0

    if from_csv:
        weather_df = pd.read_csv('weather_data.csv', index_col='time', parse_dates=True)

    else:
        r = requests.get('https://api.oikolab.com/weather',
                        params={'param': ['surface_solar_radiation'],
                                'start': request_data['start'],
                                'end': request_data['end'],
                                'lat': request_data['lat'],
                                'lon': request_data['lon'],
                                'api-key': '1a51c2dfacad40b59b950908a3c4a0dd'}
        )

        weather_data = json.loads(r.json()['data'])
        weather_df = pd.DataFrame(index=pd.to_datetime(weather_data['index'], unit='s'),
                                data=weather_data['data'],
                                columns=weather_data['columns']
        )

        # weather_df.to_csv('weather_data.csv')

    weather_df.index += pd.Timedelta(hours=2) # convert from UTC to UTC+2
                                              # mozliwe, ze trzeba bedzie sczytywac strefe czasowa z koordynatow (lat, long)

    print(weather_df.index[0])
    print(type(weather_df.index[0]))
    eff_table = pd.read_csv('efficiency_table.csv', index_col='angle')

    Wp = request_data['peak_power']
    eff = eff_table[str(request_data['azimuth'])].loc[request_data['angle']]
    radiation = weather_df['surface_solar_radiation (W/m^2)']

    E = Wp * eff * radiation / 1000
    # E = E.resample('1D').sum()

    response = {
        'time': E.index.tolist(),
        'production': E.values.tolist()
    }

    return jsonify(response)

if __name__ == '__main__':
    app.run()
