from time import sleep, time
from selenium import webdriver
from bs4 import BeautifulSoup
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from datetime import datetime
import csv
import os


def validate(date_text):
    try:
        datetime.strptime(date_text, '%d.%m.%Y')
        return True
    except ValueError:
        print("Incorrect data format, should be DD.MM.YYYY")
        return False


def insertDates():
    print("Inserting dates. All dates must be in format DD.MM.YYYY\n")
    while True:
        d1 = input("Type in first date: ")
        if not validate(d1):
            continue
        while True:
            d2 = input("Type in second date: ")
            if not validate(d2):
                continue
            else:
                return d1, d2

t0 = time()
url = "https://www.finanzen.net/termine/wirtschaftsdaten/"

# Insert dates
date1, date2 = insertDates()

# Set up a chrome driver
option = webdriver.ChromeOptions()
option.add_argument("--headless")

# For websites with pages that take forever to load, setting pageload strategy to none solves TimeoutException problem when trying to get url
capa = DesiredCapabilities.CHROME
capa["pageLoadStrategy"] = "none"

chromedriver_path = os.path.dirname(os.path.realpath(__file__)) + '/chromedriver'
driver = webdriver.Chrome(chromedriver_path, chrome_options=option, desired_capabilities=capa)
wait = WebDriverWait(driver, 20)
driver.get(url)
wait.until(EC.presence_of_element_located((By.XPATH, '//*[@id="dtTeletraderFromDate"]')))
#driver.execute_script("window.stop();")

# Setting up the file to print output
fields = ["time", "country", "relevance", "description", "previous", "forecast", "actual", "indicator"]
filename = 'output/output_' + date1 + '-' + date2 + '.csv'
f = open(filename, 'w')
w = csv.DictWriter(f, fields)
w.writeheader()

# Parsing dates to the page and loading results
fromDate = driver.find_element_by_id("dtTeletraderFromDate")
fromDate.send_keys(date1)
sleep(3)
endDate = driver.find_element_by_id("dtTeletraderEndDate")
endDate.send_keys(date2)
endDate.send_keys(Keys.RETURN)
wait.until(EC.presence_of_element_located((By.XPATH, '//*[@id="ttc_1"]/div/table')))
#driver.execute_script("window.stop();")

# Scraping the resulting table
page_source = driver.page_source
soup = BeautifulSoup(page_source, 'html.parser')
table = soup.find(id="ttc_1")
rows = table.find("tbody").findAll("tr")
for row in rows:
    header_cells = row.findAll("th")
    if header_cells != []:
        w.writerow({"time": header_cells[0].get_text()})
    else:
        cells = row.findAll("td")
        if len(cells) > 1:
            hour, country, [desc, previous, forecast, actual] = cells[0].get_text(), cells[2].get_text(), list(map(lambda x: x.get_text(), cells[4:8]))
            relevance = len(cells[3].findAll("span", {"class": "active"}))
            try:
                indicator = cells[8].find("div").get("class")[0]
            except:
                indicator = ''
            w.writerow({"time": hour, "country": country, "relevance": relevance,
                        "description": desc, "previous": previous, "forecast": forecast,
                        "actual": actual, "indicator": indicator})

f.close()
driver.quit()
print("time elapsed: ",round(time() - t0, 2), " seconds")
print("we scraped ",len(rows), " rows, average time of scraping per row ", round((time() - t0)/len(rows), 3), " seconds")
