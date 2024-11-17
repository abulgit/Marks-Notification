import os
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
import requests
import time

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

def check_ca4_marks(marks_data):
    # Skip the first two rows as they are headers
    for i, row in enumerate(marks_data):
        if i < 2:
            continue  # Skip headers

        # Ensure row has exactly 7 columns to match expected table structure
        if len(row) == 7:
            ca4_mark = row[5].strip()  # CA4 is at index 5
            # Check for non-empty and non-whitespace CA4 marks
            if ca4_mark and not ca4_mark.isspace():
                print(f"Found CA4 mark: {ca4_mark} for row: {row}")
                return True
        else:
            # Log or print a message for unexpected row structure
            print(f"Skipping row with unexpected number of columns: {row}")

    # If no CA4 marks are found
    print("No CA4 marks found")
    return False

def send_telegram_message(message):
    telegram_url = f"https://api.telegram.org/bot{telegram_token}/sendMessage"
    response = requests.post(telegram_url, data={'chat_id': chat_id, 'text': message})
    if response.status_code != 200:
        print(f"Failed to send message to Telegram: {response.text}")

try:
    # Open the website
    driver.get(url)

    # Wait for the Student button to be clickable and click it
    student_button = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.XPATH, "//a[@onclick='openLoginPage(5);']"))
    )
    student_button.click()
    time.sleep(1)
    
    # Wait for the popup and input registration number and password
    reg_no_input = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.ID, 'username'))
    )
    reg_no_input.send_keys(registration_number)
    password_input = driver.find_element(By.ID, 'password')
    password_input.send_keys(password)

    # Submit the form
    submit_button = driver.find_element(By.XPATH, "//a[@class='btn btn-success btn-lg']")
    submit_button.click()

    # Wait for the dashboard to load
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.LINK_TEXT, 'CA Marks'))
    )

    # Click on the CA mark button
    ca_mark_button = driver.find_element(By.LINK_TEXT, 'CA Marks')
    ca_mark_button.click()

    # Wait for the marks table to load
    marks_table = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.TAG_NAME, 'table'))
    )

    # Extract the marks table
    marks_data = []
    rows = marks_table.find_elements(By.TAG_NAME, 'tr')
    for row in rows:
        cols = row.find_elements(By.TAG_NAME, 'td')
        if cols:
            marks_data.append([col.text for col in cols])

    # Check CA4 marks and only send message if marks are found
    if check_ca4_marks(marks_data):
        message = "🔔 CA4 marks published! Go checkout!"
        send_telegram_message(message)

except selenium.common.exceptions.TimeoutException:
    print("Failed to load element within timeout period")
except selenium.common.exceptions.NoSuchElementException:
    print("Failed to find required element")
except Exception as e:
    print(f"An error occurred: {str(e)}")
finally:
    driver.quit()
