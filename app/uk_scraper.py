from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import time

# --- Initialize WebDriver ---
def init_driver(headless=True):
    options = Options()
    if headless:
        options.add_argument("--headless=new")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    return driver

# --- Search UK commodity page for 6-digit HS code ---
def open_uk_tariff_finder(hs_code_6_digit, driver):
    url = "https://trade-tariff.service.gov.uk/find_commodity"
    driver.get(url)
    time.sleep(2)
    try:
        search_box = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, '//*[@id="q"]'))
        )
        search_box.send_keys(hs_code_6_digit)
        time.sleep(1)
        driver.find_element(By.TAG_NAME, 'body').click()
        time.sleep(1)
        driver.find_element(By.XPATH, '//*[@id="new_search"]/div/div[3]/input').click()
        time.sleep(2)
    except Exception:
        return None
    return driver

# --- Navigate to duty calculator ---
def navigate_to_duty_calculator(hs_code, driver):
    url = "https://trade-tariff.service.gov.uk/find_commodity"
    driver.get(url)
    time.sleep(2)
    try:
        search_box = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, '//*[@id="q"]'))
        )
        search_box.send_keys(hs_code)
        driver.find_element(By.TAG_NAME, 'body').click()
        time.sleep(1)
        driver.find_element(By.XPATH, '//*[@id="new_search"]/div/div[3]/input').click()
        time.sleep(2)
        duty_calc_link = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, '//*[@id="duty-calculator-link"]'))
        )
        duty_calc_link.click()
        time.sleep(2)
        return True
    except Exception:
        return False

# --- Handle unit-based tariff input ---
def input_variable_unit(driver, quantity):
    try:
        label = WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.XPATH, '//*[@id="new_steps_measure_amount"]/div/div[2]/span'))
        )
        unit_text = label.text.strip().lower()
        field = driver.find_element(By.XPATH, '//input[contains(@id, "steps-measure-amount") and contains(@id, "-field")]')
        field.send_keys(str(quantity))
        driver.find_element(By.XPATH, '//*[@id="new_steps_measure_amount"]/button').click()
        WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.XPATH, '//*[@id="main-content"]/div/div/a[2]'))
        ).click()
        return unit_text
    except Exception:
        return None

# --- Extract tariff information ---
def extract_tariff_info(driver):
    tariff_data = {}
    try:
        option1_row = driver.find_elements(By.XPATH, '//*[@id="main-content"]/div/div/table[1]/tbody/tr[5]')
        if option1_row:
            tariff_data["Option 1 Duty Total"] = option1_row[0].find_element(By.XPATH, 'td[3]').text
        option2_row = driver.find_elements(By.XPATH, '//*[@id="main-content"]/div/div/table[2]/tbody/tr[4]')
        if option2_row:
            tariff_data["Option 2 Duty Total"] = option2_row[0].find_element(By.XPATH, 'td[3]').text
    except Exception:
        pass
    return tariff_data

# --- Main UK tariff lookup function ---
def get_uk_tariff(hs_code, country_origin, customs_value, shipping_cost, insurance_cost, quantity=None):
    driver = init_driver(headless=True)
    success = navigate_to_duty_calculator(hs_code, driver)
    if not success:
        driver.quit()
        return None, None
    try:
        wait = WebDriverWait(driver, 10)
        wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="new_steps_import_date"]/button'))).click()
        wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="new_steps_import_destination"]/div/fieldset/div[2]/div[1]/label'))).click()
        wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="new_steps_import_destination"]/button'))).click()

        origin_field = wait.until(EC.presence_of_element_located((By.XPATH, '//*[@id="steps-country-of-origin-country-of-origin-field"]')))
        origin_field.send_keys(country_origin)
        driver.find_element(By.TAG_NAME, 'body').click()
        wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="new_steps_country_of_origin"]/fieldset/button'))).click()

        if driver.find_elements(By.XPATH, '//*[@id="steps-customs-value-monetary-value-field"]'):
            driver.find_element(By.XPATH, '//*[@id="steps-customs-value-monetary-value-field"]').send_keys(str(customs_value))
            driver.find_element(By.XPATH, '//*[@id="steps-customs-value-shipping-cost-field"]').send_keys(str(shipping_cost))
            driver.find_element(By.XPATH, '//*[@id="steps-customs-value-insurance-cost-field"]').send_keys(str(insurance_cost))
            driver.find_element(By.XPATH, '//*[@id="new_steps_customs_value"]/button').click()

        unit_used = None
        if driver.find_elements(By.XPATH, '//*[@id="new_steps_measure_amount"]') and quantity is not None:
            unit_used = input_variable_unit(driver, quantity)

        tariff_data = extract_tariff_info(driver)
        driver.quit()
        return tariff_data, unit_used

    except Exception:
        driver.quit()
        return None, None
