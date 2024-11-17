import os
from dataclasses import dataclass
from typing import List, Optional
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import requests
import logging

@dataclass
class Config:
    registration_number: str
    password: str
    telegram_token: str
    chat_id: str
    base_url: str = 'https://makaut1.ucanapply.com/smartexam/public/student'
    timeout: int = 10

class MarksChecker:
    def __init__(self, config: Config):
        self.config = config
        self.setup_logging()
        self.setup_driver()
        
    def setup_logging(self):
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('marks_checker.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)

    def setup_driver(self):
        chrome_options = Options()
        chrome_options.add_argument("--headless=new")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--disable-extensions")
        chrome_options.add_argument("--disable-infobars")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--blink-settings=imagesEnabled=false")
        
        self.driver = webdriver.Chrome(options=chrome_options)
        self.wait = WebDriverWait(self.driver, self.config.timeout)

    def login(self) -> bool:
        """Handle the login process"""
        try:
            self.driver.get(self.config.base_url)
            
            # Click student button
            student_button = self.wait.until(
                EC.element_to_be_clickable((By.XPATH, "//a[@onclick='openLoginPage(5);']"))
            )
            student_button.click()
            
            # Fill login form
            self.wait.until(EC.presence_of_element_located((By.ID, 'username'))).send_keys(
                self.config.registration_number
            )
            self.driver.find_element(By.ID, 'password').send_keys(self.config.password)
            
            # Submit form
            self.driver.find_element(By.XPATH, "//a[@class='btn btn-success btn-lg']").click()
            
            return True
        except Exception as e:
            self.logger.error(f"Login failed: {str(e)}")
            self.send_telegram_notification("❌ Login failed. Please check your credentials.")
            return False

    def get_marks_data(self) -> Optional[List[List[str]]]:
        """Extract marks data from the CA marks page"""
        try:
            # Navigate to CA marks page
            self.wait.until(EC.presence_of_element_located((By.LINK_TEXT, 'CA Marks'))).click()
            
            # Get marks table
            marks_table = self.wait.until(EC.presence_of_element_located((By.TAG_NAME, 'table')))
            
            marks_data = []
            for row in marks_table.find_elements(By.TAG_NAME, 'tr'):
                cols = row.find_elements(By.TAG_NAME, 'td')
                if cols:
                    marks_data.append([col.text for col in cols])
            
            return marks_data
        except Exception as e:
            self.logger.error(f"Failed to get marks data: {str(e)}")
            return None

    def check_ca4_marks(self, marks_data: List[List[str]]) -> bool:
        """Check if CA4 marks are available"""
        if not marks_data:
            return False
            
        for row in marks_data[2:]:  # Skip headers
            if len(row) == 7 and row[5].strip():  # CA4 is at index 5
                self.logger.info(f"Found CA4 mark: {row[5]} for subject: {row[1]}")
                return True
                
        self.logger.info("No CA4 marks found")
        return False

    def send_telegram_notification(self, message: str):
        """Send notification via Telegram"""
        try:
            response = requests.post(
                f"https://api.telegram.org/bot{self.config.telegram_token}/sendMessage",
                data={'chat_id': self.config.chat_id, 'text': message}
            )
            response.raise_for_status()
            self.logger.info("Telegram notification sent successfully")
        except Exception as e:
            self.logger.error(f"Failed to send Telegram notification: {str(e)}")

    def run(self):
        """Main execution flow"""
        try:
            if not self.login():
                return

            marks_data = self.get_marks_data()
            if not marks_data:
                self.logger.error("Failed to fetch marks data")
                return

            if self.check_ca4_marks(marks_data):
                self.send_telegram_notification("🔔 CA4 marks published! Go check it out!")
            else:
                self.logger.info("No new marks found - skipping notification")

        except Exception as e:
            self.logger.error(f"An error occurred: {str(e)}")
            self.send_telegram_notification(f"❌ An error occurred: {str(e)}")
        finally:
            self.driver.quit()

def main():
    config = Config(
        registration_number=os.getenv('REGISTRATION_NUMBER'),
        password=os.getenv('PASSWORD'),
        telegram_token=os.getenv('TELEGRAM_TOKEN'),
        chat_id=os.getenv('CHAT_ID')
    )
    
    checker = MarksChecker(config)
    checker.run()

if __name__ == "__main__":
    main()
