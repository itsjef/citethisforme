#!/usr/bin/env python
import csv
import json

import selenium
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.expected_conditions import \
    presence_of_element_located
from selenium.webdriver.support.ui import WebDriverWait

success_db = {}
failure_db = {}

options = webdriver.ChromeOptions()
options.add_argument("--headless")
options.add_argument("--no-sandbox")
options.add_argument("--incognito")
options.binary_location = "/opt/google/chrome/chrome"


def load_psv(filename: str) -> dict:
    result = {}
    with open(filename) as f:
        reader = csv.reader(f, delimiter="|")

        for access_date, _type, url in reader:
            if _type not in result:
                result[_type] = {}

            if access_date not in result[_type]:
                result[_type][access_date] = set()

            result[_type][access_date].add(url)

    return result


def cite(driver, access_date, url, resource_type):
    if resource_type == "website":
        cite_website(driver, access_date, url)


def cite_website(driver, access_date, url):
    global success_db, failure_db
    driver.delete_all_cookies()

    if url in success_db or url in failure_db:
        return

    print(url)

    try:
        driver.get("https://www.citethisforme.com/cite/website")

        # Search
        driver.find_element_by_class_name("input-cite").send_keys(url + Keys.RETURN)

        wait.until(EC.url_changes(driver.current_url))
        try:
            # Not found, ignore
            driver.find_element_by_class_name("alert-error")

            print("Failed! :(")
            failure_db[url] = "URL not found"

            return
        except selenium.common.exceptions.NoSuchElementException as e:
            # Cite
            results_list = driver.find_element_by_class_name("js-results-list")
            results_list.find_element_by_xpath("li/form/button").send_keys(Keys.RETURN)

            # Continue
            wait.until(EC.url_changes(driver.current_url))
            btn = driver.find_element_by_class_name("continue-btn")
            btn.send_keys(Keys.RETURN)
            # Complete Citation
            wait.until(EC.url_changes(driver.current_url))
            btn = driver.find_element_by_class_name("continue-btn")
            btn.send_keys(Keys.RETURN)
            # Your bibliography
            wait.until(presence_of_element_located((By.CLASS_NAME, "reference-list")))

            result = driver.find_element_by_class_name(
                "highlighted"
            ).find_element_by_xpath(
                "//div[@class='reference-parts']/p/span[starts-with(@id, 'js-reference-string')]"
            )

            print("Success!")
            success_db[url] = " ".join([*result.text.split()[:-3], f"{access_date}]."])
    except Exception as err:
        print("Failed! :(")
        failure_db[url] = str(err)


if __name__ == "__main__":
    data = load_psv("data.psv")

    with webdriver.Chrome(executable_path="./chromedriver", options=options) as driver:
        wait = WebDriverWait(driver, 30)

        for _type, resources in data.items():
            for access_date, urls in resources.items():
                for url in set(urls):
                    cite(driver, access_date, url, _type)

    with open("./success.json", "w") as f:
        json.dump(success_db, f, ensure_ascii=False, indent=4)


    with open("./failure.json", "w") as f:
        json.dump(failure_db, f, ensure_ascii=False, indent=4)
