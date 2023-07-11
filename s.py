import requests

r = requests.get('https://api.oikolab.com/weather',
                 params={'param': ['temperature','wind_speed'],
                         'start': '2010-01-01',
                         'end': '2018-12-31',
                         'lat': 43.6529,
                         'lon': -79.3849,
                         'api-key': '0162070eea174926b4f794fea18e167d'}
                 )

print(r)