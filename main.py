import os
from dotenv import load_dotenv

import csv

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as ec
from webdriver_manager.firefox import GeckoDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.options import Options

load_dotenv(override=True)

USERNAME = os.environ.get('USERNAME')
PASSWORD = os.getenv('PASSWORD')

def get():
    browser_options = Options()

    driver = webdriver.Firefox(service=Service(GeckoDriverManager().install()), options=browser_options)
    driver.install_addon('uBlock0@raymondhill.net.xpi', temporary=True)
    driver.maximize_window()

    delay = 20  # seconds

    driver.get("https://fsso.ama-assn.org/login/account/login")

    driver.find_element(By.ID, 'signupGo_username').send_keys(USERNAME)
    driver.find_element(By.ID, 'signupGo_password').send_keys(PASSWORD)
    driver.find_element(By.XPATH, '//button[@name="submitButton"]').click()

    WebDriverWait(driver, delay).until(ec.url_matches('https://fsso.ama-assn.org/login/account/return'))

    driver.get('https://freida.ama-assn.org/?check_logged_in=1')



    # with open(f'{idx}.csv', 'w', encoding="utf-8") as csv_output:
    #     writer = csv.writer(csv_output, lineterminator="\n")
    # writer.writerows(data)

    driver.quit()


if __name__ == '__main__':
    get()

