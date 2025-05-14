# Refactored US tariff scraper logic for Streamlit integration (headless and form-driven)

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import time
import re

# --- Initialize WebDriver ---
def init_driver(headless=True):
    options = Options()
    if headless:
        options.add_argument('--headless')
        options.add_argument('--disable-gpu')
        options.add_argument('--no-sandbox')
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    return driver

# --- Utilities ---
def confirm_10_digit_hs_code(hs_code_6_digit: str):
    driver = open_hts_search_page(hs_code_6_digit)
    print("Browser opened to confirm the full HS code.")

    confirmed_code = input("Please enter the full 8- or 10-digit HS code you selected from the site: ").strip()
    driver.quit()

    return confirmed_code

# --- Split full HS code into parts ---
def split_confirmed_code(confirmed_code):
    confirmed_code = confirmed_code.strip().replace(".", "")
    if len(confirmed_code) == 8:
        heading_code = confirmed_code[:6]
        stat_suffix = confirmed_code[6:]
    elif len(confirmed_code) == 10:
        heading_code = confirmed_code[:8]
        stat_suffix = confirmed_code[8:]
    else:
        raise ValueError("HS code should be 8 or 10 digits long.")
    return heading_code, stat_suffix

# --- Load HTS search page ---
def open_hts_search_page(hs_code):
    url = f"https://hts.usitc.gov/search?query={hs_code}"
    driver = init_driver()
    driver.get(url)
    time.sleep(5)
    return driver

# --- Scrape all visible rows ---
def scrape_rows(driver):
    WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.ID, "table-container")))
    time.sleep(2)
    return driver.find_elements(By.XPATH, '//*[@id="table-container"]/div/table/tbody/tr')

# --- Find the best matching row for a given code ---
def find_best_match(driver, confirmed_code, rows):
    confirmed_code = confirmed_code.strip().replace(".", "")
    for idx in range(len(rows)):
        try:
            heading = driver.find_element(By.XPATH, f'//*[@id="table-container"]/div/table/tbody/tr[{idx+1}]/td[1]').text.strip().replace(".", "")
            suffix = driver.find_element(By.XPATH, f'//*[@id="table-container"]/div/table/tbody/tr[{idx+1}]/td[2]').text.strip()
            full_code = heading + suffix
            if full_code == confirmed_code:
                return idx + 1
        except:
            continue

    parent_code = confirmed_code[:-2] if len(confirmed_code) == 10 else confirmed_code
    for idx in range(len(rows)):
        try:
            heading = driver.find_element(By.XPATH, f'//*[@id="table-container"]/div/table/tbody/tr[{idx+1}]/td[1]').text.strip().replace(".", "")
            if heading == parent_code:
                return idx + 1
        except:
            continue

    return None

# --- Extract main info from selected row ---
def parse_tariff_info(driver, idx):
    try:
        description = driver.find_element(By.ID, f'descriptionID{idx-1}').text.strip()
    except:
        description = ""
    try:
        general = driver.find_element(By.XPATH, f'//*[@id="table-container"]/div/table/tbody/tr[{idx}]/td[5]').text.strip()
    except:
        general = ""
    try:
        special_element = driver.find_element(By.XPATH, f'//*[@id="table-container"]/div/table/tbody/tr[{idx}]/td[6]')
        special = special_element.text.strip()
        abbrs = special_element.find_elements(By.TAG_NAME, "abbr")
        country_mapping = {abbr.text.strip(): abbr.get_attribute("title").lower() for abbr in abbrs}
    except:
        special = ""
        country_mapping = {}
    return description, general, special, country_mapping

# --- Match special rate ---
def find_special_rate(special_text, country_mapping, origin_country):
    special_text = special_text.replace("\n", " ")
    tokens = re.split(r'(?=[\(])|(?<=\))', special_text)
    origin_country = origin_country.lower()

    country_code = None
    for code, name in country_mapping.items():
        if origin_country in name:
            country_code = code
            break

    if not country_code:
        return None

    current_rate = None
    for token in tokens:
        token = token.strip()
        if token.startswith('(') and token.endswith(')'):
            countries = [c.strip() for c in token[1:-1].split(',')]
            if country_code in countries:
                return current_rate if current_rate else "Free"
        elif token:
            current_rate = token
    return None

# --- Follow a 'See' reference ---
def handle_see_reference(driver, see_code):
    see_url = f"https://hts.usitc.gov/search?query={see_code}"
    driver.get(see_url)
    time.sleep(5)
    try:
        WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.ID, "table-container")))
        rows = driver.find_elements(By.XPATH, '//*[@id="table-container"]/div/table/tbody/tr')
        for idx in range(len(rows)):
            try:
                general = driver.find_element(By.XPATH, f'//*[@id="table-container"]/div/table/tbody/tr[{idx+1}]/td[5]').text.strip()
                special = driver.find_element(By.XPATH, f'//*[@id="table-container"]/div/table/tbody/tr[{idx+1}]/td[6]').text.strip()
                if "free" in general.lower() or "free" in special.lower():
                    return "Free"
            except:
                continue
        return None
    except:
        return None

# --- Calculate duty from rate and customs value ---
def interpret_duty(driver, applicable_rate, customs_value, quantity_input=None):
    if not applicable_rate:
        return 0

    applicable_rate = applicable_rate.lower()

    if applicable_rate.startswith("see"):
        see_code_match = re.search(r'see\s([\d\.]+)', applicable_rate)
        if see_code_match:
            see_code = see_code_match.group(1)
            applicable_rate = handle_see_reference(driver, see_code)

    if not applicable_rate:
        return 0

    if "free" in applicable_rate:
        return 0
    elif "%" in applicable_rate:
        perc = float(re.search(r'([\d\.]+)%', applicable_rate).group(1))
        return customs_value * (perc / 100)
    elif "¢/kg" in applicable_rate or "cents/kg" in applicable_rate:
        if quantity_input:
            weight = float(quantity_input)
            cents = float(re.search(r'([\d\.]+)', applicable_rate).group(1))
            return (cents / 100) * weight
    elif "¢/head" in applicable_rate or "cents/head" in applicable_rate:
        if quantity_input:
            quantity = int(quantity_input)
            cents = float(re.search(r'([\d\.]+)', applicable_rate).group(1))
            return (cents / 100) * quantity
    return 0

# --- Core callable logic ---
def get_us_tariff(confirmed_code, origin_country, customs_value, quantity_input=None):
    driver = open_hts_search_page(confirmed_code[:6])
    rows = scrape_rows(driver)
    idx = find_best_match(driver, confirmed_code, rows)
    if idx is None:
        driver.quit()
        return None, None, None

    description, general, special, mapping = parse_tariff_info(driver, idx)
    special_rate = find_special_rate(special, mapping, origin_country)
    applicable_rate = special_rate if special_rate else general

    duty = interpret_duty(driver, applicable_rate, customs_value, quantity_input)
    driver.quit()
    return description, applicable_rate, duty
