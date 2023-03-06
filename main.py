import os
import time

from dotenv import load_dotenv

import csv
import json

import requests
import urllib

from selenium import webdriver
from selenium.common import NoSuchElementException, StaleElementReferenceException
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as ec
from webdriver_manager.firefox import GeckoDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.options import Options

load_dotenv(override=True)

USERNAME = os.environ.get('USERNAME')
PASSWORD = os.getenv('PASSWORD')
SPECIALITIES = [ '43281', '43031']

FEATURES = {}
OVERVIEW = {}
PROGRAM = {}
BASIC = {}


def parse_schema(dict, path):
    with open(path, encoding="utf-8") as f:
        lines = f.read().splitlines()

        current_section = ''

        for line in lines:
            if line.isupper():
                current_section = line
                dict[current_section] = []
            else:
                dict[current_section].append(line)


def login(driver):
    driver.get("https://freida.ama-assn.org")
    menu = WebDriverWait(driver, 20).until(
        ec.element_to_be_clickable((By.XPATH, '//div[contains(@class, "ama-ribbon__sign-in-dropdown ng-tns-c15-0")]')))
    menu.click()
    sign_in = WebDriverWait(driver, 20).until(ec.element_to_be_clickable((By.XPATH, '//a[@title="Sign In"]')))
    sign_in.click()

    password_input = WebDriverWait(driver, 20).until(ec.presence_of_element_located((By.ID, 'mat-input-0')))

    password_input.send_keys(USERNAME)
    driver.find_element(By.ID, 'mat-input-1').send_keys(PASSWORD)
    driver.find_element(By.XPATH, '//button[contains(@class, "btn-primary btn-submit")]').click()

    WebDriverWait(driver, 20).until(ec.url_to_be('https://freida.ama-assn.org/?check_logged_in=1'))


def get_urls():
    url = "https://freida-admin.ama-assn.org/api/node/program"
    params = {'filter[specialty][condition][operator]': 'IN',
              'filter[specialty][condition][path]': 'field_specialty.drupal_internal__nid',
              'filter[specialty][condition][value][]': SPECIALITIES,
              'sort': 'field_address.administrative_area,field_address.locality,field_specialty.title'}
    # append each key value pair to the url without encoding the value, and splitting arrays into multiple key value pairs
    url += '?' + '&'.join(f'{k}={v}' if not isinstance(v, list) else '&'.join(f'{k}={i}' for i in v) for k, v in
                            params.items())

    print(url)

    programs = []

    while True:
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


def write_data(data):
    with open('backup.json', 'w+') as f:
        json.dump(data, f)
    with open('data.csv', 'w+') as f:
        header = ['Name', 'Link']

        for tab in [OVERVIEW, PROGRAM, FEATURES]:
            for section in tab:
                header.append(section)
                for field in tab[section]:
                    field = field.replace('//', '')
                    header.append(field)

        writer = csv.DictWriter(f, fieldnames=header)
        writer.writeheader()

        for item in data:
            to_write = {}
            for tab in item:
                to_write.update(item[tab])
            writer.writerow(to_write)


def parse_tab(driver, passed_dict):
    data = {}
    for section in passed_dict:
        for field in passed_dict[section]:
            if field.startswith('//'):
                continue

            i = 0

            while i < 10:
                try:
                    text = driver.find_element(By.XPATH,
                                               f'//td[contains(descendant-or-self::*/text(), "{field}")]/following-sibling::td[1]').text
                    data[field] = text
                    break
                except NoSuchElementException:
                    print(f'Could not find "{field}" in {section}')
                    break
                except StaleElementReferenceException:
                    print("stale element")
                    pass
                i += 1
    return data


def get():
    parse_schema(FEATURES, 'schemas/features.txt')
    parse_schema(OVERVIEW, 'schemas/overview.txt')
    parse_schema(PROGRAM, 'schemas/program.txt')
    parse_schema(BASIC, 'schemas/basic.txt')

    try:
        f = open('programs.json', 'r')
        programs = json.load(f)
    except FileNotFoundError:
        programs = get_urls()

        with open('programs.json', 'w') as f:
            json.dump(programs, f)

    data = []

    browser_options = Options()
    # browser_options.headless = True
    browser_options.add_argument("--window-size=1920,1200")
    driver = webdriver.Firefox(service=Service(GeckoDriverManager().install()), options=browser_options)
    driver.install_addon('uBlock0@raymondhill.net.xpi', temporary=True)
    driver.maximize_window()

    login(driver)

    delay = 20  # seconds

    for program_page in programs:
        while True:
            try:
                name = program_page['title']
                print(name)
                url = f"https://freida.ama-assn.org{program_page['link']}"
                driver.get(url)

                # WebDriverWait(driver, delay).until(
                #     ec.presence_of_element_located((By.XPATH, '//div[@class="ama-modal__close"]'))).click()

                WebDriverWait(driver, delay).until(
                    ec.presence_of_element_located((By.TAG_NAME, 'app-program-overview')))

                overview = parse_tab(driver, OVERVIEW if program_page['expanded'] else BASIC)

                location = driver.find_element(By.XPATH, '//div[@class="institutions__location ng-star-inserted"]')
                location_string = location.find_element(By.XPATH, './/p').text
                location_list = location_string.split('\n')
                overview['Location line 1'] = location_list[0]
                overview['Location line 2'] = location_list[1]
                overview['Location line 3'] = location_list[2]
                overview['Location line 4'] = location_list[3]

                if program_page['expanded'] is False:
                    break
                    # continue
                time.sleep(1)
                tab = WebDriverWait(driver, delay).until(
                    ec.element_to_be_clickable((By.XPATH, '//div[contains(text(), "Program & Work Schedule")]')))
                driver.execute_script("arguments[0].click();", tab)
                WebDriverWait(driver, delay).until(
                    ec.presence_of_element_located((By.TAG_NAME, 'app-program-work-schedule')))
                program = parse_tab(driver, PROGRAM)

                program_faculty_table = driver.find_element(By.ID, 'program_faculty')
                program_faculty = program_faculty_table.find_element(By.TAG_NAME, 'tbody')

                rows = program_faculty.find_elements(By.TAG_NAME, 'tr')
                full = rows[0].find_elements(By.TAG_NAME, 'td')
                part = rows[1].find_elements(By.TAG_NAME, 'td')
                total = rows[2].find_elements(By.TAG_NAME, 'td')

                program['Full-time paid physician'] = full[1].text
                program['Full-time paid non-physician'] = full[2].text

                program['Part-time paid physician'] = part[1].text
                program['Part-time paid non-physician'] = part[2].text

                program['Total physician'] = total[1].text
                program['Total non-physician'] = total[2].text

                tab = WebDriverWait(driver, delay).until(
                    ec.element_to_be_clickable((By.XPATH, '//div[contains(text(), "Features & Benefits")]')))
                driver.execute_script("arguments[0].click();", tab)
                WebDriverWait(driver, delay).until(
                    ec.presence_of_element_located((By.TAG_NAME, 'app-program-features-benefits')))
                features = parse_tab(driver, FEATURES)

                compensation_table = driver.find_element(By.ID, 'compensation')
                program_faculty = compensation_table.find_element(By.TAG_NAME, 'tbody')

                row = program_faculty.find_element(By.TAG_NAME, 'tr')
                cols = row.find_elements(By.TAG_NAME, 'td')

                features['Salary compensation'] = cols[1].text
                features['Vacation days'] = cols[2].text
                features['Sick days'] = cols[3].text

                meta = {
                    'Name': name,
                    'Link': url
                }

                data.append({'meta': meta, 'overview': overview, 'program': program, 'features': features})
                # driver.execute_script("window.localStorage.clear();")
                break
            except Exception as e:
                print(e)

    driver.quit()
    write_data(data)


if __name__ == '__main__':
    get()
