import os
import time
import yaml
import logging

from dotenv import load_dotenv
from webdriver_manager.chrome import ChromeDriverManager

# # Log in to LinkedIn using credentials from .env
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import ElementClickInterceptedException
from selenium.common.exceptions import NoSuchElementException, TimeoutException

from ai.ai_bot import generate_cover_letter, generate_answer_with_gpt

# # Load environment variables from .env file (LinkedIn credentials)
load_dotenv("resources/.env")
LINKEDIN_USERNAME = os.getenv("LINKEDIN_USERNAME")
LINKEDIN_PASSWORD = os.getenv("LINKEDIN_PASSWORD")


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


def load_config():
    # Load the config.yaml file containing answers for the application
    try:
        with open("resources/config.yaml", "r") as file:
            config = yaml.safe_load(file)
        print("Config file loaded successfully.")
        return config
    except Exception as e:
        print(f"Failed to load config file: {e}")
        raise


def apply_to_jobs(driver, config):
    try:
        # Scroll to load more job listings
        print("Scrolling down to load job listings...")
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(3)

        # Find all job cards in the list
        jobs = driver.find_elements(By.CLASS_NAME, "job-card-container__link")
        easy_apply_jobs = []

        # Loop through job listings and click each one to open the side panel
        for index, job in enumerate(jobs):
            input("Clicking next job card")
            try:
                # Scroll the job card into view and click it
                print(f"Clicking job card {index+1}")
                driver.execute_script("arguments[0].scrollIntoView(true);", job)
                WebDriverWait(driver, 5).until(EC.element_to_be_clickable(job)).click()
                time.sleep(3)  # Wait for the side panel to load

                # Now check the side panel for the Easy Apply button
                try:
                    easy_apply_button = WebDriverWait(driver, 5).until(
                        EC.element_to_be_clickable((By.CLASS_NAME, "jobs-apply-button"))
                    )
                    driver.execute_script("arguments[0].click();", easy_apply_button)
                    print("Easy Apply button clicked!")

                    # time.sleep(3)

                    # After clicking, fill out the application form
                    fill_application_form(driver, config["application_answers"])

                except Exception:
                    print(
                        f"No Easy Apply button found for job {index+1}. Skipping to next job."
                    )
                    continue  # If no Easy Apply button is found, skip to the next job

            except Exception as e:
                print(f"Error clicking job card {index+1}: {e}")
                continue

        # Apply to Easy Apply jobs
        if not easy_apply_jobs:
            print("No Easy Apply jobs found.")
            return

    except Exception as e:
        print(f"Error while processing jobs: {e}")


# Setup logging to capture unanswered questions
logging.basicConfig(
    filename="unanswered_questions.log",
    level=logging.INFO,
    format="%(message)s",
)


def fill_application_form(driver, answers):
    try:
        while True:
            # Fill the form fields
            fill_form_fields(driver, answers)

            try:
                # Click the "Next" button if it exists
                next_button = WebDriverWait(driver, 15).until(
                    EC.element_to_be_clickable(
                        (
                            By.XPATH,
                            '//button[contains(@aria-label, "Continue to next step") or contains(@aria-label, "Next")]',
                        )
                    )
                )
                try:
                    next_button.click()
                    print("Clicked on 'Next' to proceed to the next form.")
                except ElementClickInterceptedException:
                    # If click is intercepted, retry clicking without scrolling
                    print("Click intercepted, retrying without scrolling...")
                    driver.execute_script("arguments[0].click();", next_button)

                # Wait for the next form fields to load
                time.sleep(2)  # Adjust based on form loading times
                WebDriverWait(driver, 15).until(
                    EC.presence_of_element_located(
                        (By.XPATH, "//input | //select | //textarea")
                    )
                )

            except TimeoutException:
                # No "Next" button found, try the "Review" button
                try:
                    review_button = WebDriverWait(driver, 10).until(
                        EC.element_to_be_clickable(
                            (
                                By.XPATH,
                                '//button[contains(@aria-label, "Review your application") or contains(aria-label, "Review")]',
                            )
                        )
                    )
                    try:
                        # import pdb

                        # pdb.set_trace()
                        review_button.click()
                        print("Clicked on 'Review' button.")
                    except ElementClickInterceptedException:
                        # If click is intercepted, retry clicking without scrolling
                        print("Click intercepted, retrying without scrolling...")
                        driver.execute_script("arguments[0].click();", review_button)

                    # Wait a moment for the review page to process
                    time.sleep(2)

                    handle_follow_checkbox(driver)
                    input("check follow check box")

                    # Look for the "Submit" button after review
                    try:
                        submit_button = WebDriverWait(driver, 10).until(
                            EC.element_to_be_clickable(
                                (
                                    By.XPATH,
                                    '//button[contains(@aria-label, "Submit application") or contains(aria-label, "Submit")]',
                                )
                            )
                        )
                        try:
                            submit_button.click()
                            print("Application submitted successfully.")
                        except ElementClickInterceptedException:
                            print("Click intercepted, retrying without scrolling...")
                            driver.execute_script(
                                "arguments[0].click();", submit_button
                            )

                        close_popup_if_present(driver)

                        break
                    except (NoSuchElementException, TimeoutException):
                        print("No 'Submit' button found after the review step.")
                        break

                except (NoSuchElementException, TimeoutException):
                    print("No 'Next', 'Review', or 'Submit' button found.")
                    break

    except Exception as e:
        print(f"Error while filling out the application form: {e}")


def fill_form_fields(driver, config):
    try:
        # Find all label elements in the form
        labels = driver.find_elements(By.XPATH, "//label")

        for label in labels:
            question_text = ""
            try:
                # Get the label text (it might be inside a <span>, or not)
                try:
                    span_element = label.find_element(By.XPATH, ".//span")
                    question_text = (
                        span_element.text.strip()
                        if span_element
                        else label.text.strip()
                    )
                except:
                    question_text = (
                        label.text.strip()
                    )  # No <span>, use label's text directly

                if not question_text or "Search" in question_text:
                    continue  # Skip irrelevant labels

                # Find the input/textarea/select that comes immediately after the label
                input_element = None
                try:
                    input_element = label.find_element(
                        By.XPATH,
                        "./following-sibling::select | ./following-sibling::input | ./following-sibling::textarea",
                    )
                except:
                    pass

                if input_element is None:
                    # If not a direct sibling, look for an input/select/textarea within the same container
                    try:
                        input_element = label.find_element(
                            By.XPATH,
                            "../following-sibling::input | ../following-sibling::select | ../following-sibling::textarea",
                        )
                    except:
                        pass

                if input_element is None or not input_element.is_displayed():
                    # Fallback: Try finding an input within the same parent div (sometimes forms are structured this way)
                    try:
                        input_element = label.find_element(
                            By.XPATH,
                            "following::input | following::select | following::textarea",
                        )
                    except:
                        pass

                if input_element is None or not input_element.is_displayed():
                    continue  # If no corresponding input or element is not visible, skip this label

                # Match the question with the config
                answer_found = False
                for key, qa_pair in config.items():
                    if qa_pair["question"].lower() == question_text.lower():
                        answer = qa_pair["answer"]
                        answer_found = True
                        break

                if answer_found:
                    # Handle <select> dropdowns
                    if input_element.tag_name == "select":
                        select = Select(input_element)
                        try:
                            select.select_by_visible_text(answer)
                            print(f"Selected option for: {question_text}")
                        except:
                            available_options = [opt.text for opt in select.options]
                            print(
                                f"Available options for '{question_text}': {available_options}"
                            )
                            # Attempt to select by partial match
                            for option in select.options:
                                if answer.lower() in option.text.lower():
                                    select.select_by_visible_text(option.text)
                                    print(
                                        f"Partially matched and selected option for: {question_text}"
                                    )
                                    break
                            else:
                                print(
                                    f"Option '{answer}' not found for question '{question_text}'."
                                )

                    elif (
                        input_element.tag_name == "input"
                        and input_element.get_attribute("type") == "checkbox"
                    ):
                        # Handle checkboxes
                        is_checked = input_element.is_selected()
                        if answer.lower() == "yes" and not is_checked:
                            input_element.click()
                        elif answer.lower() == "no" and is_checked:
                            input_element.click()

                    elif (
                        input_element.tag_name == "input"
                        or input_element.tag_name == "textarea"
                    ):
                        # Handle text inputs and textareas
                        if not input_element.get_attribute("value"):
                            input_element.send_keys(answer)
                            print(f"Filled answer for: {question_text}")
                        else:
                            print(
                                f"Filled {qa_pair['answer']} for: {qa_pair['question']}"
                            )

                    else:
                        print(
                            f"Unhandled field type: {input_element.tag_name} for question: {question_text}"
                        )

                else:
                    print(f"Unanswered question found: {question_text} (logged)")

            except Exception as e:
                if question_text:
                    print(f"Error filling field '{question_text}': {e}")
                else:
                    print(f"Error while locating a field or label: {e}")

        print("Application form filled out.")

    except Exception as e:
        print(f"Error filling out the application form: {e}")


def close_popup_if_present(driver):
    try:
        # Wait for the modal pop-up to appear
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located(
                (By.XPATH, "//div[@class='artdeco-modal__content ember-view']")
            )
        )

        # Locate and click the "Not now" button to close the pop-up
        not_now_button = driver.find_element(
            By.XPATH, "//button//span[text()='Not now']"
        )
        not_now_button.click()
        print("Closed the pop-up window successfully.")

    except Exception as e:
        print(f"No pop-up found or error closing the pop-up: {e}")


def handle_follow_checkbox(driver):
    try:
        # Locate the 'Follow' checkbox using its ID
        follow_checkbox = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "follow-company-checkbox"))
        )

        # Scroll the checkbox into view before interacting with it
        driver.execute_script("arguments[0].scrollIntoView(true);", follow_checkbox)
        time.sleep(1)  # Allow time for the scroll

        # Check if the checkbox is selected and uncheck it if needed
        if follow_checkbox.is_selected():
            follow_checkbox.click()  # Uncheck the checkbox
            print("Unchecked the 'Follow' checkbox.")
        else:
            print("'Follow' checkbox was already unchecked.")
        input("Check follow box")

    except NoSuchElementException as e:
        print(f"Error while handling the 'Follow' checkbox: {e}")
    except TimeoutException as e:
        print(f"'Follow' checkbox not found in time: {e}")
    except Exception as e:
        print(f"Unexpected error while handling the 'Follow' checkbox: {e}")


# Example function to scrape job description using Selenium
def scrape_job_description(driver, job_url):
    driver.get(job_url)

    try:
        job_description_element = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "job-description"))
        )
        job_description = job_description_element.text
        return job_description
    except Exception as e:
        print(f"Error while scraping job description: {e}")
        return ""


# if __name__ == "__main__":
#     # Load the config file for answers to questions
#     config = load_config()

#     # Set up the Selenium WebDriver
#     driver = setup_driver()  # Ensure setup_driver function is properly set up
#     linkedin_login(driver, LINKEDIN_USERNAME, LINKEDIN_PASSWORD)

#     # Wait for manual login
#     input("Please manually log in and apply filters. Press Enter to continue...")

#     # Try to apply to jobs using Easy Apply
#     try:
#         apply_to_jobs(driver, config)
#     finally:
#         # Always close the driver at the end
#         driver.quit()
