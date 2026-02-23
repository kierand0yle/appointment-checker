import os
import time
import logging
import smtplib
from datetime import datetime
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
        self.chrome_options.add_argument("--disable-gpu")
        self.chrome_options.add_argument("--window-size=1920,1080")
        self.driver = None

    def setup_driver(self):
        logger.info("Setting up Chrome driver...")
        self.driver = webdriver.Chrome(options=self.chrome_options)
        self.driver.implicitly_wait(10)
        logger.info("Chrome driver ready")

    def notify_result(self, appointments_available, available_slots):
        if appointments_available and available_slots:
            print("\n🎉 APPOINTMENTS ARE AVAILABLE! 🎉")
            print("Available slots:")
            # Group slots by date
            slots_by_date = {}
            for slot in available_slots:
                if slot['date'] not in slots_by_date:
                    slots_by_date[slot['date']] = []
                slots_by_date[slot['date']].append(slot['time'])
            
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
                
                receiver_emails = [email.strip() for email in receiver_emails_str.split(",")]
                subject = "🚨 Swedish Embassy Appointments Available!"
                
                body = "Appointments are now available at the Swedish Embassy!\n\nAvailable slots:\n"
                for date, times in slots_by_date.items():
                    body += f"\n{date}: {', '.join(sorted(times))}"
                body += f"\n\nBook now: {self.base_url}"
                body += "\n\n⚠️ These slots go fast - book immediately!"
                
                msg = MIMEText(body)
                msg['Subject'] = subject
                msg['From'] = sender_email
                msg['To'] = ", ".join(receiver_emails)
                
                with smtplib.SMTP(smtp_server, port) as server:
                    server.starttls()
                    server.login(sender_email, sender_password)
                    server.send_message(msg)
                logger.info(f"Email notification sent to {len(receiver_emails)} recipient(s)")
            except Exception as e:
                logger.error(f"Failed to send email notification: {str(e)}")
        else:
            print("\n❌ No appointments available at this time.")

    def click_element_safely(self, by, value, description, wait=10):
        try:
            element = WebDriverWait(self.driver, wait).until(
                EC.element_to_be_clickable((by, value))
            )
            element.click()
            logger.info(f"✓ {description}")
            # Small delay to let page transitions complete
            time.sleep(1)
            return True
        except TimeoutException:
            logger.error(f"✗ Timeout waiting for: {description}")
            self._save_debug_screenshot(description)
            return False
        except Exception as e:
            logger.error(f"✗ Error clicking {description}: {str(e)}")
            self._save_debug_screenshot(description)
            return False

    def _save_debug_screenshot(self, context):
        """Save a screenshot for debugging when something goes wrong."""
        try:
            filename = f"/tmp/debug_{context.replace(' ', '_')}.png"
            self.driver.save_screenshot(filename)
            logger.info(f"Debug screenshot saved: {filename}")
            # Also log the current page source snippet for debugging
            page_text = self.driver.find_element(By.TAG_NAME, "body").text[:500]
            logger.info(f"Page content: {page_text[:200]}...")
        except Exception:
            pass

    def check_appointments(self):
        try:
            self.setup_driver()
            logger.info("Starting appointment check...")
            
            # Navigate to the base URL
            self.driver.get(self.base_url)
            logger.info("Loaded base URL")
            time.sleep(2)  # Wait for initial page load

            # Step 1: Click "Boka ny tid"
            if not self.click_element_safely(By.CSS_SELECTOR, "input[title='Boka ny tid']", "Boka ny tid button"):
                return False, []

            # Step 2: Check "AcceptInformationStorage"
            if not self.click_element_safely(By.ID, "AcceptInformationStorage", "Accept Information Storage checkbox"):
                return False, []

            # Step 3: Click "Nästa"
            if not self.click_element_safely(By.CSS_SELECTOR, "input[value='Nästa']", "First Nästa button"):
                return False, []

            # Step 4: Click service category radio button
            if not self.click_element_safely(By.ID, "ServiceCategoryCustomers_0__ServiceCategoryId", "Service Category radio"):
                return False, []

            # Step 5: Click "Nästa" again
            if not self.click_element_safely(By.CSS_SELECTOR, "input[value='Nästa']", "Second Nästa button"):
                return False, []

            # Step 6: Click conditional agreement checkbox
            if not self.click_element_safely(By.ID, "RequiresConditionalAgreement", "Conditional Agreement checkbox"):
                return False, []

            # Step 7: Click "Nästa" again
            if not self.click_element_safely(By.CSS_SELECTOR, "input[value='Nästa']", "Third Nästa button"):
                return False, []

            # Step 8: Click time search button
            if not self.click_element_safely(By.NAME, "TimeSearchFirstAvailableButton", "Time Search button", wait=15):
                return False, []

            # Step 9: Wait for results to load
            logger.info("Waiting for appointment results...")
            time.sleep(3)

            # Step 10: Check for results
            try:
                # First check if there's a "no appointments" message
                try:
                    no_appt = self.driver.find_element(By.XPATH, "//label[contains(text(), 'Inga lediga tider kunde hittas.')]")
                    if no_appt:
                        logger.info("No appointments available (system confirmed)")
                        return False, []
                except NoSuchElementException:
                    logger.info("No 'no appointments' message found - checking for available slots...")

                # Look for the timetable
                try:
                    timetable = WebDriverWait(self.driver, 15).until(
                        EC.presence_of_element_located((By.CLASS_NAME, "timetable"))
                    )
                    logger.info("Timetable found!")
                except TimeoutException:
                    logger.warning("No timetable found - page may have changed")
                    self._save_debug_screenshot("no_timetable")
                    return False, []

                # Get all available dates and times
                # Use dynamic year matching instead of hardcoded year
                current_year = str(datetime.now().year)
                available_slots = []
                
                # Get all date headers - match any year pattern (YYYY-)
                headers = self.driver.find_elements(By.XPATH, "//th[@id and (contains(@id, '2025-') or contains(@id, '2026-') or contains(@id, '2027-'))]")
                if not headers:
                    # Fallback: try matching any th with a date-like id
                    headers = self.driver.find_elements(By.XPATH, f"//th[@id and contains(@id, '{current_year}-')]")
                
                date_ids = {header.get_attribute('id'): header.text.replace('\n', ' ') for header in headers}
                logger.info(f"Found {len(date_ids)} date column(s): {list(date_ids.values())}")

                # Find all time slots
                time_cells = self.driver.find_elements(By.XPATH, "//div[@data-function='timeTableCell']")
                logger.info(f"Found {len(time_cells)} time slot(s)")
                
                for cell in time_cells:
                    from_dt = cell.get_attribute('data-fromdatetime')
                    if from_dt:
                        date = from_dt.split()[0]
                        time_str = from_dt.split()[1] if len(from_dt.split()) > 1 else ""
                        # Match slot to a date column, or add it anyway
                        date_label = date_ids.get(date, date)
                        available_slots.append({
                            'date': date_label,
                            'time': time_str[:5]  # Format HH:MM
                        })

                if available_slots:
                    logger.info(f"🎉 Found {len(available_slots)} available time slot(s)!")
                    return True, available_slots
                else:
                    logger.info("Timetable present but no clickable slots found")
                    return False, []

            except Exception as e:
                logger.error(f"Error checking appointment results: {str(e)}")
                self._save_debug_screenshot("error_checking_results")
                return False, []

        except Exception as e:
            logger.error(f"Error during appointment check: {str(e)}")
            return False, []
        finally:
            if self.driver:
                self.driver.quit()
                logger.info("Browser closed")

    def run(self):
        result = self.check_appointments()
        # Handle both tuple and bare return values safely
        if isinstance(result, tuple):
            appointments_available, available_slots = result
        else:
            appointments_available = result
            available_slots = []
        self.notify_result(appointments_available, available_slots)

if __name__ == "__main__":
    scraper = SwedishEmbassyScraper()
    scraper.run()
