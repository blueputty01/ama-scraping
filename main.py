import os
from dotenv import load_dotenv

import csv
import json

import requests
import urllib

from selenium import webdriver
from selenium.common import NoSuchElementException
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as ec
from webdriver_manager.firefox import GeckoDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.options import Options

load_dotenv(override=True)

USERNAME = os.environ.get('USERNAME')
PASSWORD = os.getenv('PASSWORD')

FEATURES = {}
OVERVIEW = {}
PROGRAM = {}


def parse_schema(dict, path):
    with open(path) as f:
        lines = f.read().splitlines()

        current_section = ''

        for line in lines:
            if line.isupper():
                current_section = line
                dict[current_section] = []
            else:
                dict[current_section].append(line)


def login(driver):
    driver.get("https://fsso.ama-assn.org/login/account/login")

    driver.find_element(By.ID, 'signupGo_username').send_keys(USERNAME)
    driver.find_element(By.ID, 'signupGo_password').send_keys(PASSWORD)
    driver.find_element(By.XPATH, '//button[@name="submitButton"]').click()

    WebDriverWait(driver, 20).until(ec.url_to_be('https://fsso.ama-assn.org/login/account/return'))

    driver.get("https://freida.ama-assn.org")
    sign_in_menu = driver.find_element(By.XPATH, '//span[contains(text(), "Sign In")]')
    driver.execute_script("arguments[0].click();", sign_in_menu)
    sign_in = driver.find_element(By.XPATH, '//a[contains(@title, "Sign In")]')
    driver.execute_script("arguments[0].click();", sign_in)

    WebDriverWait(driver, 20).until(ec.url_to_be('https://freida.ama-assn.org/?check_logged_in=1'))


def get_urls():
    url = "https://freida-admin.ama-assn.org/api/node/program"
    params = {'filter[specialty][condition][operator]': 'IN',
              'filter[specialty][condition][path]': 'field_specialty.drupal_internal__nid',
              'filter[specialty][condition][value][]': '43521',
              'sort': 'field_address.administrative_area,field_address.locality,field_specialty.title'}
    url += f'?={urllib.parse.urlencode(params)}'

    programs = []

    while True:
        print(url)
        r = requests.get(url)
        response = r.json()

        data = response['data']
        for item in data:
            attributes = item['attributes']

            title = attributes['title']
            link = attributes['path']
            expanded = attributes['field_expanded_listing']

            programs.append({'title': title, 'link': link, 'expanded': expanded})
            print(title, link, expanded)

        links = response['links']
        if 'next' not in links:
            break

        url = links['next']['href']

    return programs


def print_data(data):
    with open('backup.json') as f:
        json.dump(data, f)
    with open('data.csv', 'w') as f:
        writer = csv.writer(f)

        header = []

        for tab in [OVERVIEW, PROGRAM, FEATURES]:
            for section in tab:
                for field in section:
                    header.append(field)
            header.append(' ')

        writer.writerow(header)

        for item in data:
            to_write = []
            for tab in item:
                for section in tab:
                    for field in section:
                        to_write.append(field)
                to_write.append(' ')

            writer.writerow(to_write)


def parse_tab(driver, passed_dict):
    data = []
    for section in passed_dict:
        for field in passed_dict[section]:
            try:
                text = driver.find_element(By.XPATH, f'//td[contains(text(), {field})]/following-sibling::td[1]').text
                data.append(text)
                print(text)
            except NoSuchElementException:
                print(f'Could not find "{field}" in {section}')
    return data


def get():
    parse_schema(FEATURES, 'schemas/features.txt')
    parse_schema(OVERVIEW, 'schemas/overview.txt')
    parse_schema(PROGRAM, 'schemas/program.txt')

    try:
        f = open('programs.json', 'r')
        programs = json.load(f)
    except FileNotFoundError:
        programs = get_urls()

        with open('programs.json', 'w') as f:
            json.dump(programs, f)

    data = []

    browser_options = Options()

    driver = webdriver.Firefox(service=Service(GeckoDriverManager().install()), options=browser_options)
    driver.install_addon('uBlock0@raymondhill.net.xpi', temporary=True)
    driver.maximize_window()

    login(driver)

    delay = 20  # seconds

    for program in programs:
        url = f"https://freida.ama-assn.org{program['link']}"
        driver.get(url)

        overview = parse_tab(driver, OVERVIEW)

        if program['expanded'] is False:
            continue

        driver.find_element(By.XPATH, '//div[contains(text(), "Program & Work Schedule")]').click()
        program = parse_tab(driver, PROGRAM)

        driver.find_element(By.XPATH, '//div[contains(text(), "Features & Benefits")]').click()
        features = parse_tab(driver, FEATURES)

        data.append({'overview': overview, 'program': program, 'features': features})
    driver.quit()
    print_data(data)


if __name__ == '__main__':
    get()
