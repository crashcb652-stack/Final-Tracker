import pandas as pd
import csv
from datetime import datetime
import logging
import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options


# --- 1. INITIALIZATION & LOGGING ---
logging.basicConfig(filename="scraper_log.txt", level=logging.INFO,
                    format="%(asctime)s - %(message)s")

target_uni = input("Enter the University Name (use dashes-for-spaces): ").strip()
formatted_uni = target_uni.replace(" ", "-").lower()
now = datetime.now().strftime("%Y-%m-%d_%H-%M")

# --- 2. BROWSER SETUP ---
chrome_options = Options()
chrome_options.add_argument("--disable-extensions")
chrome_options.add_argument("--dns-prefetch-disable")
chrome_options.add_argument("-- disable-blink-features=AutomationControlled")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.binary_location = "/usr/bin/google-chrome"
chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36")
chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
chrome_options.add_experimental_option("useAutomationExtension", False)

service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service, options=chrome_options)
driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

    # --- 3. EXECUTION ---
url = f"https://scholarshipdb.net/scholarships?q={formatted_uni}"
driver.get(url)
wait = WebDriverWait(driver, 60)
print(f"Optimizing connection for {target_uni} ---")
scholarship_list = []

try:
    logging.info(f"STARTING SCRAPE FOR: {target_uni}")
    while True:
        wait.until(EC.presence_of_all_elements_located((By.TAG_NAME, "a")))
        items = driver.find_elements(By.CSS_SELECTOR, "h4 a, .list-item a, .item a")

        for item in items:
            href = item.get_attribute("href")
            title = item.text.strip()
            if href and not any(d["URL"] == href for d in scholarship_list):
                scholarship_list.append({"Scholarship Name": title, "URL": href})

                print(f"DEBUGG: Collected {len(scholarship_list)} links...")
                
        try:
            next_button = driver.find_element(By.PARTIAL_LINK_TEXT, "Next")
            driver.execute_script("arguements[0].scrollIntoView();", next_button)
            time.sleep(1)
            next_button.click()
            time.sleep(3)
        
        except:
            logging.info(f"Finished all pages for {target_uni}. Total found: {len(scholarship_list)}")
            break
    
        # --- 4. DATA EXPORT ---      
    if scholarship_list:
        filename = f"{target_uni}_results_{datetime.now().strftime('%Y%m%d_%H%M')}.csv"
        df = pd.DataFrame(scholarship_list)
        df.to_csv(filename, index=False, encoding="utf-8")

        logging.info(f"Scraped {scholarship_list} unique links for {target_uni}")
        print(f"\nMISSION SUCCESS: {len(scholarship_list)} scholarships saved to {filename}")
    else:
        logging.warning(f"Empty: No scholarships for {target_uni}")
        print("CRITICAL FAILURE: No data collected.")

except Exception as e:
    logging.error(f"SYSTEM CRASH: {e}")
    print(f"CRITICAL FAILURE on line {e.__traceback__.tb_lineno}: {e}")

# Safely closes the Chrome window 
finally:
    driver.quit()