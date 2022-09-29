from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import Select
from selenium.webdriver.common.by import By
import pandas as pd

import logging

logging.basicConfig(
    filename="logs/load_industry.log",
    level=logging.DEBUG,
    format="%(asctime)s:%(levelname)s:%(message)s",
)


def download_industry_data(url, industry_list_path):
    # Creating selenium driver
    driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()))
    driver.get(url)

    # finding dropdown menu
    industry_selector = Select(driver.find_element(By.NAME, "industry"))
    # finding options to dropdown menu
    options = [option.get_attribute("value") for option in industry_selector.options]

    # iterating through the options and saving them
    for option in options:
        industry_selector = Select(driver.find_element(By.NAME, "industry"))
        driver.implicitly_wait(5)
        industry_selector.select_by_visible_text(option)
        driver.implicitly_wait(5)
        button = driver.find_element(By.CLASS_NAME, "buttons-csv")
        driver.implicitly_wait(5)
        button.click()
        logging.info(f"industry info downloaded for {option} industry")

    ind_df = pd.DataFrame(options, columns=["industries"])
    ind_df.to_csv(industry_list_path, index=False)
    logging.info(f"Csv that contains industries is saved to {industry_list_path}")

    driver.quit()
    return 1
