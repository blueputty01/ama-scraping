import os
from dotenv import load_dotenv

import csv

import requests
import urllib

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
    url = "https://freida-admin.ama-assn.org/api/node/program"
    params = {'filter[specialty][condition][operator]': 'IN',
              'filter[specialty][condition][path]': 'field_specialty.drupal_internal__nid',
              'filter[specialty][condition][value][]': '43521', }
    url += f'?={urllib.parse.urlencode(params)}'

    programs = []

    while True:
        r = requests.get(url)
        response = r.json()

        data = response['data']
        for item in data:
            attributes = item['attributes']

            title = attributes['title']
            link = attributes['path']
            expanded = attributes['field_expanded']

            programs.append({'title': title, 'link': link, 'expanded': expanded})
            print(title, link, expanded)

        next_url_dict = response['links']['next']
        if next is None:
            break

        url = next_url_dict['href']

    data = []

    browser_options = Options()

    driver = webdriver.Firefox(service=Service(GeckoDriverManager().install()), options=browser_options)
    driver.install_addon('uBlock0@raymondhill.net.xpi', temporary=True)
    driver.maximize_window()

    delay = 20  # seconds

    for program in programs:
        if program['expanded'] is False:
            data.append('Not expanded')
            continue
        driver.get(program['link'])

        driver.execute_script('window.localStorage.clear();')

    # with open(f'{idx}.csv', 'w', encoding="utf-8") as csv_output:
    #     writer = csv.writer(csv_output, lineterminator="\n")
    # writer.writerows(data)

    driver.quit()


if __name__ == '__main__':
    get()
