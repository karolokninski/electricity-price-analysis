from selenium import webdriver
from selenium.webdriver.common.by import By
import pandas as pd
import datetime
import time
import os

# Start the Selenium webdriver and load the URL
driver = webdriver.Chrome()

# Define the start and end dates
start_date = datetime.date(2023, 3, 10)
end_date = datetime.date(2023, 5, 4)

# Set the Xpath and base directory
xpath = '//*[@id="footable_kontrakty_godzinowe"]'
base_dir = '/home/karol/python/scraper/tge-prices'

# Create folder for data
os.makedirs(base_dir, exist_ok=True)

# Loop through each date in the range
current_date = start_date
while current_date <= end_date:
    # Print the date
    print(f'Searching for data from: {current_date}')

    # Format the date as 'dd-mm-yyyy'
    date = current_date.strftime('%d-%m-%Y')

    # Set the URL
    url = f'https://tge.pl/electricity-dam?dateShow={date}' 
    driver.get(url)

    # Wait for the table to load and retrieve its HTML
    table = driver.find_element(By.XPATH, xpath)
    table_html = table.get_attribute('outerHTML')

    # Use Pandas to read the HTML table and convert it to a dataframe
    df = pd.read_html(table_html)[0]

    # Save the dataframe to a CSV file
    df.to_csv(f'{base_dir}/hourly_contract_prices-{date}.csv', index=False)
    
    # Wait for one second before moving to the next date
    time.sleep(1)

    # Print status
    print('Done.')

    # Move to the next date
    current_date += datetime.timedelta(days=1)

# Close the Selenium webdriver
driver.quit()
