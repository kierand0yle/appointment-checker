import os
import logging
import smtplib
from email.mime.text import MIMEText
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.chrome.options import Options

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class SwedishEmbassyScraper:
    def __init__(self):
        self.base_url = "https://ventus.enalog.se/Booking/Booking/Index/UDDLondon"
        self.chrome_options = Options()
        self.chrome_options.add_argument("--headless")
        self.chrome_options.add_argument("--no-sandbox")
        self.chrome_options.add_argument("--disable-dev-shm-usage")
        self.driver = None

    def setup_driver(self):
        logger.info("Setting up Chrome driver...")
        self.driver = webdriver.Chrome(options=self.chrome_options)
        self.driver.implicitly_wait(10)

    def notify_result(self, appointments_available, available_slots):
        # Always print the result
        if appointments_available and available_slots:
            print("\n🎉 APPOINTMENTS ARE AVAILABLE! 🎉")
            print("Available slots:")
            # Group slots by date
            slots_by_date = {}
            for slot in available_slots:
                if slot['date'] not in slots_by_date:
                    slots_by_date[slot['date']] = []
                slots_by_date[slot['date']].append(slot['time'])
            
            # Print slots grouped by date
            for date, times in slots_by_date.items():
                print(f"  {date}: {', '.join(sorted(times))}")
            print(f"\nVisit {self.base_url} to book your appointment.")
            
            # Send email notification
            try:
                smtp_server = "smtp.gmail.com"
                port = 587
                sender_email = os.environ.get("SENDER_EMAIL")
                sender_password = os.environ.get("SENDER_PASSWORD")
                
                if not sender_email or not sender_password:
                    logger.error("Email credentials not found in environment variables")
                    return
                
                receiver_emails_str = os.environ.get("RECEIVER_EMAIL")
                if not receiver_emails_str:
                    logger.error("Receiver email not found in environment variables")
                    return
                
                # Split email addresses and remove any whitespace
                receiver_emails = [email.strip() for email in receiver_emails_str.split(",")]
                subject = "Swedish Embassy Appointments Available!"
                
                # Create detailed message body
                body = "Appointments are now available at the Swedish Embassy!\n\nAvailable slots:\n"
                for date, times in slots_by_date.items():
                    body += f"\n{date}: {', '.join(sorted(times))}"
                body += f"\n\nVisit {self.base_url} to book your appointment."
                
                msg = MIMEText(body)
                msg['Subject'] = subject
                msg['From'] = sender_email
                msg['To'] = ", ".join(receiver_emails)
                
                with smtplib.SMTP(smtp_server, port) as server:
                    server.starttls()
                    server.login(sender_email, sender_password)
                    # Send to each recipient using BCC to protect privacy
                    msg['To'] = sender_email  # Set sender as main recipient
                    msg['Bcc'] = ", ".join(receiver_emails)
                    server.send_message(msg)
                logger.info("Email notification sent successfully")
            except Exception as e:
                logger.error(f"Failed to send email notification: {str(e)}")
        else:
            print("\n❌ No appointments available at this time.")

    def click_element_safely(self, by, value, description):
        try:
            element = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((by, value))
            )
            element.click()
            logger.info(f"Successfully clicked {description}")
            return True
        except TimeoutException:
            logger.error(f"Timeout waiting for {description}")
            return False
        except Exception as e:
            logger.error(f"Error clicking {description}: {str(e)}")
            return False

    def check_appointments(self):
        try:
            self.setup_driver()
            logger.info("Starting appointment check...")
            
            # Navigate to the base URL
            self.driver.get(self.base_url)
            logger.info("Loaded base URL")

            # Step 1: Click "Boka ny tid"
            if not self.click_element_safely(By.CSS_SELECTOR, "input[title='Boka ny tid']", "Boka ny tid button"):
                return False

            # Step 2: Check "AcceptInformationStorage"
            if not self.click_element_safely(By.ID, "AcceptInformationStorage", "Accept Information Storage checkbox"):
                return False

            # Step 3: Click "Nästa"
            if not self.click_element_safely(By.CSS_SELECTOR, "input[value='Nästa']", "First Nästa button"):
                return False

            # Step 4: Click service category radio button
            if not self.click_element_safely(By.ID, "ServiceCategoryCustomers_0__ServiceCategoryId", "Service Category radio"):
                return False

            # Step 5: Click "Nästa" again
            if not self.click_element_safely(By.CSS_SELECTOR, "input[value='Nästa']", "Second Nästa button"):
                return False

            # Step 6: Click conditional agreement checkbox
            if not self.click_element_safely(By.ID, "RequiresConditionalAgreement", "Conditional Agreement checkbox"):
                return False

            # Step 7: Click "Nästa" again
            if not self.click_element_safely(By.CSS_SELECTOR, "input[value='Nästa']", "Third Nästa button"):
                return False

            # Step 8: Click time search button
            if not self.click_element_safely(By.NAME, "TimeSearchFirstAvailableButton", "Time Search button"):
                return False

            # Step 9: Check for no appointments label
            try:
                # First check if there's a "no appointments" message
                try:
                    self.driver.find_element(By.XPATH, "//label[contains(text(), 'Inga lediga tider kunde hittas.')]")
                    logger.info("No appointments available")
                    return False, []
                except NoSuchElementException:
                    pass

                # Look for the timetable
                timetable = WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.CLASS_NAME, "timetable"))
                )

                # Get all available dates and times
                available_slots = []
                
                # Get all date headers
                headers = self.driver.find_elements(By.XPATH, "//th[@id and contains(@id, '2025-')]")
                date_ids = {header.get_attribute('id'): header.text.replace('\n', ' ') for header in headers}

                # Find all time slots
                time_cells = self.driver.find_elements(By.XPATH, "//div[@data-function='timeTableCell']")
                
                for cell in time_cells:
                    date = cell.get_attribute('data-fromdatetime').split()[0]
                    time = cell.get_attribute('data-fromdatetime').split()[1]
                    if date in date_ids:
                        available_slots.append({
                            'date': date_ids[date],
                            'time': time[:5]  # Format HH:MM
                        })

                if available_slots:
                    logger.info(f"Found {len(available_slots)} available time slots")
                    return True, available_slots
                else:
                    logger.info("No appointments found in timetable")
                    return False, []

            except Exception as e:
                logger.error(f"Error checking appointments: {str(e)}")
                return False, []

        except Exception as e:
            logger.error(f"Error during appointment check: {str(e)}")
            return False
        finally:
            if self.driver:
                self.driver.quit()

    def run(self):
        appointments_available, available_slots = self.check_appointments()
        self.notify_result(appointments_available, available_slots)

if __name__ == "__main__":
    scraper = SwedishEmbassyScraper()
    scraper.run()
