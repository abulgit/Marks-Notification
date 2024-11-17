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
registration_number = '16500222030'
password = 'Abulmac@#555'
telegram_token = os.getenv('TELEGRAM_TOKEN')
url = 'https://makaut1.ucanapply.com/smartexam/public/student' 
chat_id = '1394339679'


chrome_options = Options()
chrome_options.add_argument("--headless")  # Ensures headless mode
chrome_options.add_argument("--no-sandbox")  # Optional: helps prevent certain errors
chrome_options.add_argument("--disable-dev-shm-usage")  # Optional: reduces resource usage

driver = webdriver.Chrome(options=chrome_options)

def check_ca4_marks(marks_data):
    # Add debug printing
    print("Analyzing marks data...")
    for row in marks_data:
        # Skip header rows
        if 'SEMESTER' in ' '.join(row) or 'Paper Code' in ' '.join(row):
            print(f"Skipping header row: {row}")
            continue
            
        # Look for CA 4 column (index 5 since zero-based)
        if len(row) > 5:  # Must have at least 6 columns
            ca4_mark = row[5].strip()  # CA4 is at index 5
            print(f"Checking CA4 mark: '{ca4_mark}' for row: {row}")
            if ca4_mark and ca4_mark != '' and not ca4_mark.isspace():
                print(f"Found CA4 mark: {ca4_mark}")
                return True
    print("No CA4 marks found")
    return False





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
    reg_no_input = driver.find_element(By.ID, 'username')
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

    # Check CA4 marks and prepare message
    if check_ca4_marks(marks_data):
        message = "🔔 CA4 marks published! Go checkout!"
    else:
        message = "No new CA4 marks available yet."

    # Send the message to Telegram
    telegram_url = f"https://api.telegram.org/bot{telegram_token}/sendMessage"
    response = requests.post(telegram_url, data={'chat_id': chat_id, 'text': message})
    
    # Verify if message was sent successfully
    if response.status_code != 200:
        print(f"Failed to send message to Telegram: {response.text}")

except selenium.common.exceptions.TimeoutException:
    message = "Failed to load element within timeout period"
    requests.post(telegram_url, data={'chat_id': chat_id, 'text': message})
except selenium.common.exceptions.NoSuchElementException:
    message = "Failed to find required element"
    requests.post(telegram_url, data={'chat_id': chat_id, 'text': message})
except Exception as e:
    message = f"An error occurred: {str(e)}"
    requests.post(telegram_url, data={'chat_id': chat_id, 'text': message})
finally:
    driver.quit()
