# API for PV calculator app

### 1. Build app

`docker build -t api .`

### 2. Run container

`docker run --env API_SECRET=API_key_here --env WEATHER_API_SECRET=API_key_here --env AZURE_DB_PWD=db_pwd_here -it --rm -p 80:80 api`

### Calculate PV production and profit

http://api-rce.azurewebsites.net:80/api/estimate

## Get data from /api/estimate

### Request format for /api/estimate

```
request_data = {
        'start': '2023-07-10',
        'end': '2023-07-11',
        'lat': 52.1077,
        'lon': 22.1306,
        'azimuth': 0,
        'angle': 30,
        'peak_power': 7000,
}
```

### Response format for /api/estimate

```
{'production': [5539.3835,
    5196.7755,
    1957.893,
    1101.9715,
    1288.7035],
'profit': [2.9061081881649997,
    2.90353864479,
    2.87628672135,
    2.8320537209999994,
    2.2942306657899993,
    1.9017918577000001],
'time': ['2023-07-11 01:00:00',
    '2023-07-11 02:00:00',
    '2023-07-11 03:00:00',
    '2023-07-11 04:00:00',
    '2023-07-11 05:00:00',]
}
```

### Simple request code

```
import requests
import pandas as pd

url = 'http://api-rce.azurewebsites.net:80/estimate'
request_data = {
        'start': '2023-07-10',
        'end': '2023-07-11',
        'lat': 52.1077,
        'lon': 22.1306,
        'azimuth': 0,
        'angle': 30,
        'peak_power': 7000,
}

response = requests.post(url, json=request_data, headers={'Authorization': 'Bearer API_key_here'})
```

### Save emails

http://api-rce.azurewebsites.net:80/api/save_email


### Request format for /api/estimate

```
request_data = {
    'email': ['test@test.pl', 'example@mail.com']
}
```

### Response format for /api/estimate

```
response = {
    'status': 200
}
```