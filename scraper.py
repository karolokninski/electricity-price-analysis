import urllib.request
import time
import datetime
import os

base_dir = os.getcwd() + '/prices'

# Create folder for data
os.makedirs(base_dir, exist_ok=True)

# Iterate over the years 2020 to 2023
for year in range(2018, 2020):
    # Iterate over the months 1 to 12
    for month in range(1, 13):
        # Calculate the first and last day of the month
        first_day = datetime.date(year, month, 1)
        last_day = first_day + datetime.timedelta(days=32)
        last_day = last_day.replace(day=1)
        last_day -= datetime.timedelta(days=1)

        # Status
        print(f'Downloading data from {year}-{month}')

        first_day = first_day.strftime('%Y%m%d')
        last_day = last_day.strftime('%Y%m%d')

        # Replace with the actual download link
        download_link = f'https://www.pse.pl/getcsv/-/export/csv/EN_PRICE/data_od/{first_day}/data_do/{last_day}'

        print(download_link)

        # Download the file
        urllib.request.urlretrieve(download_link, f'{base_dir}/prices-{year}-{month}.csv')

        # Wait for the download to complete
        while True:
            time.sleep(1)
            if f'{base_dir}/prices-{year}-{month}.csv.crdownload' not in os.listdir():
                break

        # The download is now complete
        print('Download finished!')
