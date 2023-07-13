1. Build app

`docker build -t api .`

2. Run container

`docker run --env API_SECRET=API_key_here --env WEATHER_API_SECRET=API_key_here -it --rm -p 80:80 api`

3. Simple request code

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