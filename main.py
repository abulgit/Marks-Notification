import os
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
import requests
import time
import selenium  # Added to handle exceptions

# Configuration
registration_number = os.getenv('REGISTRATION_NUMBER')
password = os.getenv('PASSWORD')
telegram_token = os.getenv('TELEGRAM_TOKEN')
chat_id = os.getenv('CHAT_ID')
url = 'https://makaut1.ucanapply.com/smartexam/public/student'

chrome_options = Options()
chrome_options.add_argument("--headless=new")  # Modern headless mode
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--disable-extensions")
chrome_options.add_argument("--disable-infobars")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--blink-settings=imagesEnabled=false")  # Disable images

driver = webdriver.Chrome(options=chrome_options)

def retry_until_success(func, retries=3, delay=5):
    for attempt in range(retries):
        try:
            return func()
        except TimeoutException as e:
            if attempt < retries - 1:
                print(f"Retrying after TimeoutException ({attempt + 1}/{retries})...")
                time.sleep(delay)
            else:
                raise e

def check_ca4_marks(marks_data):
    for i, row in enumerate(marks_data[2:]):  # Skip headers
        if len(row) == 7:
            ca4_mark = row[5].strip()
            if ca4_mark and not ca4_mark.isspace():
                print(f"Found CA4 mark: {ca4_mark} for row: {row}")
                return True
    print("No CA4 marks found")
    return False

def send_telegram_message(message):
    telegram_url = f"https://api.telegram.org/bot{telegram_token}/sendMessage"
    response = requests.post(telegram_url, data={'chat_id': chat_id, 'text': message})
    if response.status_code != 200:
        print(f"Failed to send message to Telegram: {response.text}")

try:
    driver.get(url)

    retry_until_success(
        lambda: WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//a[@onclick='openLoginPage(5);']"))
        ).click()
    )

    retry_until_success(
        lambda: WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, 'username'))
        ).send_keys(registration_number)
    )
    driver.find_element(By.ID, 'password').send_keys(password)
    driver.find_element(By.XPATH, "//a[@class='btn btn-success btn-lg']").click()

    retry_until_success(
        lambda: WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.LINK_TEXT, 'CA Marks'))
        )
    ).click()

    marks_table = retry_until_success(
        lambda: WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, 'table'))
        )
    )

    rows = marks_table.find_elements(By.TAG_NAME, 'tr')
    marks_data = [[col.text for col in row.find_elements(By.TAG_NAME, 'td')] for row in rows if row.find_elements(By.TAG_NAME, 'td')]

    if check_ca4_marks(marks_data):
        send_telegram_message("🔔 CA4 marks published! Go checkout!")

except TimeoutException:
    print("TimeoutException: Failed to load element within timeout period")
except NoSuchElementException:
    print("NoSuchElementException: Failed to find required element")
except Exception as e:
    print(f"An unexpected error occurred: {str(e)}")
finally:
    driver.quit()
