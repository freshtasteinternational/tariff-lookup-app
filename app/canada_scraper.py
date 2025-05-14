from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import time
import re
from datetime import datetime

# --- Initialize WebDriver ---
def init_driver(headless=False):
    options = Options()
    if headless:
        options.add_argument('--headless')
        options.add_argument('--disable-gpu')
        options.add_argument('--no-sandbox')
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    driver.maximize_window()
    return driver

# --- Utilities ---
UNIT_NAMES = {
    "kg": "kilograms",
    "item": "items",
    "piece": "pieces",
    "litre": "litres",
    "dozen": "dozens",
    "head": "heads",
    "unit": "units",
    "ton": "tons",
    "g": "grams",
    "l": "litres"
    # Add more as needed
}

def parse_tariff_text(text):
    if "free" in text.lower():
        return 0.0, "value", "Free"

    percent_match = re.search(r"([0-9]+(?:\.[0-9]+)?)\s*%", text)
    if percent_match:
        return float(percent_match.group(1)) / 100, "value", "Ad valorem (%)"

    cent_match = re.search(r"([0-9]+(?:\.[0-9]+)?)\s*\u00a2/([a-zA-Z]+)", text)
    if cent_match:
        rate = float(cent_match.group(1)) / 100
        unit = cent_match.group(2).lower()
        return rate, unit, f"Unit-based (cent per {unit})"

    dollar_match = re.search(r"\$([0-9]+(?:\.[0-9]+)?)\s*/\s*([a-zA-Z]+)", text)
    if dollar_match:
        rate = float(dollar_match.group(1))
        unit = dollar_match.group(2).lower()
        return rate, unit, f"Unit-based (dollar per {unit})"

    return 0.0, "value", "Unknown format"

def get_available_countries(driver):
    driver.get("https://www.tariffinder.ca/en/getStarted")
    time.sleep(3)
    try:
        WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, '//*[@id="q-app"]/div/div[1]/main/div[2]/div[1]/div/div[3]/div[3]/span'))
        ).click()
        time.sleep(2)

        WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, '//*[@id="q-app"]/div/div[1]/main/div[2]/div[1]/div/div[4]/div[2]/div/div[2]/div/div'))
        ).click()
        time.sleep(2)

        elements = driver.find_elements(By.XPATH, '//div[@class="q-item-label"]')
        return [elem.text.strip() for elem in elements if elem.text.strip()]
    except Exception:
        return []

def confirm_10_digit_hs_code(hs_code_6_digit, country_code):
    driver = init_driver()
    driver.get("https://www.tariffinder.ca/en/getStarted")
    time.sleep(3)
    try:
        WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, '//*[@id="q-app"]/div/div[1]/main/div[2]/div[1]/div/div[3]/div[3]/span'))
        ).click()
        time.sleep(2)

        WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, '//*[@id="q-app"]/div/div[1]/main/div[2]/div[1]/div/div[4]/div[2]/div/div[2]/div/div'))
        ).click()
        time.sleep(1)

        driver.find_element(By.XPATH, f"//div[contains(text(), '{country_code}')]" ).click()
        time.sleep(1)

        search_box = driver.find_element(By.XPATH, '//*[@id="q-app"]/div/div[1]/main/div[2]/div[1]/div/div[5]/div[2]/div/div[2]/div/input')
        search_box.send_keys(hs_code_6_digit)
        time.sleep(1)

        driver.find_element(By.XPATH, '//*[@id="tms_fta_navigation_1"]').click()
        time.sleep(3)

        driver.quit()
        return True
    except Exception:
        driver.quit()
        return False

def open_tariff_page(driver, hs_code_10_digit, country_code):
    hs_chunk = hs_code_10_digit[:8]
    url = f"https://www.tariffinder.ca/en/search/import/{country_code}/{hs_chunk}/{hs_code_10_digit}"
    driver.get(url)
    time.sleep(4)
    return driver

def scrape_mfn_tariff(driver):
    try:
        elem = driver.find_element(By.XPATH, '//*[@id="q-app"]/div/div[1]/main/div/div[6]/div/div[1]/div/table/thead/tr/th[2]')
        return parse_tariff_text(elem.text.strip()) + ("MFN",)
    except Exception:
        return 0.0, "value", "MFN (Error)", "MFN"

def scrape_tariff(driver, force_mfn=False):
    if force_mfn:
        return scrape_mfn_tariff(driver)
    try:
        rows = driver.find_elements(By.XPATH, '//*[@id="q-app"]/div/div[1]/main/div/div[6]/div[2]/div[2]/div/table/tbody/tr')
        current_year = datetime.now().year
        best_rate = None
        for row in rows:
            cells = row.find_elements(By.TAG_NAME, 'td')
            if len(cells) < 3:
                continue
            try:
                year = int(cells[0].text.strip())
                if year > current_year:
                    continue
                rates = []
                for cell in cells[1:3]:
                    text = cell.text.strip()
                    if "free" in text.lower():
                        rates.append(0.0)
                    else:
                        match = re.search(r"([0-9]+(?:\.[0-9]+)?)", text)
                        if match:
                            rates.append(float(match.group(1)))
                if rates:
                    candidate = min(rates)
                    if best_rate is None or candidate < best_rate:
                        best_rate = candidate
            except Exception:
                continue
        if best_rate is not None:
            return best_rate / 100, "value", "FTA - Ad valorem (%)", "FTA"
        else:
            raise Exception("No valid FTA found")
    except Exception:
        return scrape_mfn_tariff(driver)
