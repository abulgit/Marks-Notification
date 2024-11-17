import os
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
import requests
from concurrent.futures import ThreadPoolExecutor

class FastMarksChecker:
    def __init__(self):
        self.setup_config()
        self.setup_driver()
        
    def setup_config(self):
        self.config = {
            'registration_number': os.getenv('REGISTRATION_NUMBER'),
            'password': os.getenv('PASSWORD'),
            'telegram_token': os.getenv('TELEGRAM_TOKEN'),
            'chat_id': os.getenv('CHAT_ID'),
            'url': 'https://makaut1.ucanapply.com/smartexam/public/student'
        }

    def setup_driver(self):
        options = Options()
        options.add_argument('--headless=new')
        options.add_argument('--disable-gpu')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-extensions')
        options.add_argument('--disable-infobars')
        options.add_argument('--blink-settings=imagesEnabled=false')
        options.add_argument('--disable-javascript')  # Disable if site works without JS
        options.add_argument('--disable-images')
        options.add_argument('--disable-css')  # Disable if site works without CSS
        options.page_load_strategy = 'eager'  # Don't wait for full page load
        
        self.driver = webdriver.Chrome(options=options)
        self.driver.set_script_timeout(5)
        self.driver.set_page_load_timeout(10)
        self.wait = WebDriverWait(self.driver, 5)  # Reduced timeout

    def login(self):
        try:
            self.driver.get(self.config['url'])
            
            # Click student button and fill form
            self.wait.until(EC.element_to_be_clickable(
                (By.XPATH, "//a[@onclick='openLoginPage(5);']")
            )).click()
            
            self.wait.until(EC.presence_of_element_located(
                (By.ID, 'username')
            )).send_keys(self.config['registration_number'])
            
            self.driver.find_element(By.ID, 'password').send_keys(self.config['password'])
            self.driver.find_element(By.XPATH, "//a[@class='btn btn-success btn-lg']").click()
            return True
        except Exception as e:
            print(f"Login failed: {e}")
            return False

    def send_notification(self, message):
        try:
            requests.post(
                f"https://api.telegram.org/bot{self.config['telegram_token']}/sendMessage",
                data={'chat_id': self.config['chat_id'], 'text': message},
                timeout=5  # Add timeout
            )
        except Exception as e:
            print(f"Notification failed: {e}")

    def check_marks(self):
        try:
            # Navigate to marks page
            self.wait.until(EC.presence_of_element_located(
                (By.LINK_TEXT, 'CA Marks')
            )).click()
            
            # Get marks table quickly
            table = self.wait.until(EC.presence_of_element_located((By.TAG_NAME, 'table')))
            rows = table.find_elements(By.TAG_NAME, 'tr')[2:]  # Skip headers
            
            # Check for CA4 marks
            for row in rows:
                cols = row.find_elements(By.TAG_NAME, 'td')
                if len(cols) == 7 and cols[5].text.strip():
                    return True
            return False
        except Exception as e:
            print(f"Check failed: {e}")
            return False

    def run(self):
        try:
            if not self.login():
                return

            if self.check_marks():
                self.send_notification("🔔 CA4 marks published!")
                
        finally:
            self.driver.quit()

if __name__ == "__main__":
    checker = FastMarksChecker()
    checker.run()
