# import time
# import yaml
import logging
import os
from dotenv import load_dotenv

# # Log in to LinkedIn using credentials from .env
# from selenium.webdriver.common.by import By
# from selenium.webdriver.support.ui import WebDriverWait
# from selenium.webdriver.support import expected_conditions as EC


# from selenium.webdriver.common.by import By
# from selenium.webdriver.support.ui import WebDriverWait
# from selenium.webdriver.support import expected_conditions as EC


from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import Select
from selenium.common.exceptions import NoSuchElementException, TimeoutException

# from selenium.webdriver.common.by import By
# from selenium.webdriver.support.ui import WebDriverWait
# from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

# # Load environment variables from .env file (LinkedIn credentials)
load_dotenv("resources/.env")
LINKEDIN_USERNAME = os.getenv("LINKEDIN_USERNAME")
LINKEDIN_PASSWORD = os.getenv("LINKEDIN_PASSWORD")


# # Load the entire config file (search parameters and application answers)
# def load_config():
#     # Get the absolute path of the script
#     script_dir = os.path.dirname(os.path.abspath(__file__))

#     # Construct the full path to config.yaml
#     config_path = os.path.join(script_dir, "../resources/config.yaml")

#     if not os.path.exists(config_path):
#         raise FileNotFoundError(f"Config file not found: {config_path}")

#     # Load the config.yaml file
#     with open(config_path, "r") as file:
#         config = yaml.safe_load(file)
#     return config


def setup_driver():
    chrome_options = Options()
    # Disable headless mode for normal browsing
    # chrome_options.add_argument("--headless")

    # Add necessary options
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")

    # Mimic a real user-agent
    chrome_options.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    )

    # Disable Selenium detection
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option("useAutomationExtension", False)

    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)

    # Hide webdriver flag
    driver.execute_script(
        "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
    )

    return driver


def linkedin_login(driver, LINKEDIN_USERNAME, LINKEDIN_PASSWORD):
    driver.get("https://www.linkedin.com/login")

    try:
        # Wait until the username field is present
        username_field = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "username"))
        )
        print("Username field found!")

        # Wait until the password field is present
        password_field = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "password"))
        )
        print("Password field found!")

        # Wait until the login button is clickable
        login_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, '//button[@type="submit"]'))
        )
        print("Login button found!")

        # Send keys and click
        username_field.send_keys(LINKEDIN_USERNAME)
        password_field.send_keys(LINKEDIN_PASSWORD)
        login_button.click()
        print("Login form submitted!")

        # Wait for LinkedIn feed page to load after login
        WebDriverWait(driver, 15).until(EC.url_contains("/feed"))
        print("Logged in successfully!")

    except Exception as e:
        print(f"Login failed: {e}")


# # Search for jobs using parameters from config.yaml
# def search_jobs(driver, search_params):
#     job_title = search_params["job_title"]
#     location = search_params["location"]

#     # Construct the LinkedIn search URL for jobs with the job title and location
#     search_url = f"https://www.linkedin.com/jobs/search/?keywords={job_title}&location={location}"
#     driver.get(search_url)
#     print(f"Navigating to job search page: {search_url}")
#     time.sleep(3)

#     try:
#         # Locate and click the "All filters" button using its aria-label
#         filters_button = WebDriverWait(driver, 10).until(
#             EC.element_to_be_clickable(
#                 (
#                     By.XPATH,
#                     '//button[contains(@aria-label, "Show all filters")]',
#                 )
#             )
#         )
#         filters_button.click()
#         print("All filters button clicked!")
#         time.sleep(2)

#         # Locate the scrollable modal container
#         filters_modal_container = driver.find_element(
#             By.XPATH, '//div[contains(@class, "artdeco-modal__content")]'
#         )
#         print("Filters modal container found.")

#         # Scroll within the modal to find the "Easy Apply" filter text
#         easy_apply_text_found = False

#         for _ in range(10):  # Scroll in increments until the filter is found
#             try:
#                 # Locate the Easy Apply text on the left side of the modal
#                 easy_apply_text = WebDriverWait(filters_modal_container, 5).until(
#                     EC.presence_of_element_located(
#                         (
#                             By.XPATH,
#                             '//h3[contains(text(), "Easy Apply")]',
#                         )
#                     )
#                 )
#                 driver.execute_script(
#                     "arguments[0].scrollIntoView(true);", easy_apply_text
#                 )
#                 print("Easy Apply text found!")
#                 easy_apply_text_found = True
#                 break
#             except Exception as e:
#                 # Scroll within the modal container if not found
#                 driver.execute_script(
#                     "arguments[0].scrollTop += 300;", filters_modal_container
#                 )
#                 print("Scrolling down inside the filters modal...")
#                 time.sleep(1)

#         if not easy_apply_text_found:
#             print("Easy Apply text not found after scrolling.")
#             return []

#         # Once the Easy Apply text is found, locate the toggle checkbox on the right side
#         try:
#             easy_apply_toggle = filters_modal_container.find_element(
#                 By.XPATH,
#                 '//div[@data-control-name="filter_detail_select"]//input[@type="checkbox"]',
#             )
#             driver.execute_script(
#                 "arguments[0].scrollIntoView(true);", easy_apply_toggle
#             )
#             print("Easy Apply toggle found!")

#             # Check if the Easy Apply filter is toggled off, and then click to turn it on
#             is_checked = easy_apply_toggle.get_attribute("aria-checked")

#             # If it's not selected (false), click the checkbox
#             if is_checked == "false":
#                 driver.execute_script("arguments[0].click();", easy_apply_toggle)
#                 print("Easy Apply filter toggled on!")
#             elif is_checked == "true":
#                 print("Easy Apply filter is already selected.")
#             else:
#                 print("Could not determine the state of the Easy Apply filter.")

#         except Exception as e:
#             print(f"Failed to locate the Easy Apply toggle: {e}")
#             return []

#         # Apply the filter by clicking the "Show results" button
#         apply_filters_button = WebDriverWait(driver, 10).until(
#             EC.element_to_be_clickable(
#                 (By.XPATH, '//button[@data-control-name="all_filters_apply"]')
#             )
#         )
#         apply_filters_button.click()
#         print("Filters applied!")
#         time.sleep(5)

#         # Scroll to load more jobs (you can adjust this to load more listings)
#         driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
#         time.sleep(3)

#         # Find job listings with the Easy Apply button
#         jobs = driver.find_elements(By.CLASS_NAME, "job-card-container__link")
#         easy_apply_jobs = []

#         for job in jobs:
#             try:
#                 # Look for the Easy Apply button inside each job listing
#                 easy_apply_button = job.find_element(
#                     By.XPATH, ".//span[text()='Easy Apply']"
#                 )

#                 # Extract the link (href attribute) of the job if Easy Apply is found
#                 job_link = job.get_attribute("href")
#                 easy_apply_jobs.append(job_link)  # Append the job link

#             except Exception as e:
#                 print(f"Failed to detect Easy Apply button: {e}")
#                 pass  # If the Easy Apply button is not found, skip the job

#         return easy_apply_jobs

#     except Exception as e:
#         print(f"Failed to apply the Easy Apply filter: {e}")
#         return []


# # Answer common LinkedIn application questions using config.yaml answers
# def answer_application_questions(driver, answers):
#     try:
#         for key, value in answers.items():
#             question = value["question"]
#             answer = value["answer"]

#             # Find and answer text fields or checkboxes
#             try:
#                 field = driver.find_element(
#                     By.XPATH, f'//input[@aria-label="{question}"]'
#                 )
#                 if isinstance(answer, bool):  # Checkbox
#                     if answer and not field.is_selected():
#                         field.click()
#                 else:
#                     field.send_keys(answer)

#             except Exception as e:
#                 print(f"Could not find or answer the question '{question}': {e}")

#         print("All application questions answered.")
#     except Exception as e:
#         print(f"Error answering application questions: {e}")


# # Apply to a job and fill out any required application form fields
# def apply_to_job(driver, job_link, answers):
#     driver.get(job_link)
#     time.sleep(3)

#     # Click on Apply button
#     try:
#         apply_button = driver.find_element(By.CLASS_NAME, "jobs-apply-button--top-card")
#         apply_button.click()
#         time.sleep(2)

#         # Answer application questions
#         answer_application_questions(driver, answers)

#         # Submit the application (if applicable)
#         try:
#             submit_button = driver.find_element(
#                 By.XPATH, '//button[contains(text(),"Submit application")]'
#             )
#             submit_button.click()
#             print("Application submitted!")
#         except Exception as e:
#             print(f"Error submitting the application: {e}")

#     except Exception as e:
#         print(f"Error during application process: {e}")


# # Set up WebDriver using ChromeDriverManager and Chrome options
# def setup_driver():
#     chrome_options = Options()
#     # chrome_options.add_argument("--headless")  # Still use headless mode for automation
#     chrome_options.add_argument("--no-sandbox")
#     chrome_options.add_argument("--disable-dev-shm-usage")
#     chrome_options.add_argument("--disable-gpu")

#     # Add options to make the browser appear less like a bot
#     chrome_options.add_argument("--disable-blink-features=AutomationControlled")
#     chrome_options.add_argument("--incognito")
#     chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
#     chrome_options.add_experimental_option("useAutomationExtension", False)

#     # Set up the ChromeDriver service
#     service = Service(ChromeDriverManager(driver_version="128.0.6613.137").install())
#     driver = webdriver.Chrome(service=service, options=chrome_options)

#     # Disable the navigator.webdriver flag
#     driver.execute_script(
#         "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
#     )

#     return driver


# # Main function to run the bot
# def main():
#     # Load configuration from config.yaml
#     config = load_config()

#     # Set up WebDriver
#     driver = setup_driver()

#     # driver.get("https://www.google.com")
#     # print(driver.title)
#     # driver.quit()

#     # Close the browser
#     # driver.quit()

#     try:
#         # Log in to LinkedIn using credentials from .env
#         linkedin_login(driver, LINKEDIN_USERNAME, LINKEDIN_PASSWORD)

#         # Search for Easy Apply jobs based on parameters from config.yaml
#         search_params = config["search_parameters"]
#         easy_apply_jobs = search_jobs(driver, search_params)

#         # Iterate over job listings and apply
#         max_applications = config["settings"]["max_applications"]
#         for job in easy_apply_jobs[:max_applications]:
#             job_link = job.get_attribute("href")
#             print(f"Applying to job: {job_link}")

#             # Apply to the job using answers from config.yaml
#             apply_to_job(driver, job_link, config["application_answers"])

#     finally:
#         # Close the browser
#         driver.quit()


# if __name__ == "__main__":
#     main()