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

from ai.ai_bot import generate_cover_letter, generate_answer_for_question

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
        time.sleep(2)

        # Find all job cards in the list
        # jobs = driver.find_elements(By.CLASS_NAME, "job-card-container__link")
        # jobs = driver.find_elements(By.CSS_SELECTOR, ".job-card-container--clickable")
        jobs = get_all_job_cards(driver)
        easy_apply_jobs = []

        import pdb

        pdb.set_trace()

        # Loop through job listings and click each one to open the side panel
        for index, job in enumerate(jobs):
            # input("Clicking next job card")
            try:
                # Scroll the job card into view and click it
                print(f"Clicking job card {index+1}")
                driver.execute_script("arguments[0].scrollIntoView(true);", job)
                WebDriverWait(driver, 3).until(EC.element_to_be_clickable(job)).click()
                time.sleep(2)  # Wait for the side panel to load

                # Now check the side panel for the Easy Apply button
                try:
                    # scrape job details for ai
                    job_description = scrape_job_description(driver)

                    easy_apply_button = WebDriverWait(driver, 5).until(
                        EC.element_to_be_clickable((By.CLASS_NAME, "jobs-apply-button"))
                    )
                    driver.execute_script("arguments[0].click();", easy_apply_button)
                    print("Easy Apply button clicked!")

                    # time.sleep(3)

                    # After clicking, fill out the application form
                    fill_application_form(driver, config)

                except Exception:
                    print(
                        f"No Easy Apply button found for job {index+1}. Skipping to next job."
                    )
                    continue  # If no Easy Apply button is found, skip to the next job

            except Exception as e:
                print(f"Error clicking job card {index+1}: {e}")
                continue

        # click to next page
        click_next_page(driver)

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
                next_button = WebDriverWait(driver, 5).until(
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
                        review_button.click()
                        print("Clicked on 'Review' button.")
                    except ElementClickInterceptedException:
                        # If click is intercepted, retry clicking without scrolling
                        print("Click intercepted, retrying without scrolling...")
                        driver.execute_script("arguments[0].click();", review_button)

                    # Wait a moment for the review page to process
                    time.sleep(2)

                    handle_follow_checkbox(driver)
                    # input("check follow check box")

                    # Look for the "Submit" button after review
                    try:
                        submit_button = WebDriverWait(driver, 15).until(
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
        form = driver.find_element(By.XPATH, "//form")
        labels = form.find_elements(
            By.XPATH, ".//label[not(contains(@class, 'visually-hidden'))]"
        )
        # Find all label elements in the form
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

                existing_value = input_element.get_attribute("value")
                if existing_value or existing_value == "Select an option":
                    print(
                        f"Skipping {question_text}, already filled with value: {existing_value}"
                    )
                    continue

                # Match the question with the config
                answer = config.get(question_text)

                if not answer:
                    import pdb

                    pdb.set_trace()
                    # input("Answer not found generating...")
                    answer = generate_answer_for_question(question_text)
                    if answer:
                        # input_element.send_keys(answer)
                        print(f"AI-generated answer for: {question_text}")
                        answer_found = True

                if answer:
                    # Handle radio buttons (Yes/No)
                    if input_element.get_attribute("type") == "radio":
                        yes_radio = form.find_element(
                            By.XPATH,
                            f"//input[@type='radio' and @value='Yes'][@name='{input_element.get_attribute('name')}']",
                        )
                        no_radio = form.find_element(
                            By.XPATH,
                            f"//input[@type='radio' and @value='No'][@name='{input_element.get_attribute('name')}']",
                        )

                        # Select appropriate radio button based on the answer
                        if answer.lower() == "yes" and not yes_radio.is_selected():
                            yes_radio.click()
                            print(f"Selected 'Yes' for: {question_text}")
                        elif answer.lower() == "no" and not no_radio.is_selected():
                            no_radio.click()
                            print(f"Selected 'No' for: {question_text}")
                        continue  # Continue after handling radio buttons

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
                                f"Filled {config[{question_text}]} for: {question_text}"
                            )

                    else:
                        print(
                            f"Unhandled field type: {input_element.tag_name} for question: {question_text}"
                        )

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
        # Locate the 'Follow' checkbox (it's hidden, so we need to interact with the label)
        label_element = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located(
                (By.XPATH, "//label[@for='follow-company-checkbox']")
            )
        )

        # Scroll to the label to make sure it's in view
        driver.execute_script("arguments[0].scrollIntoView(true);", label_element)

        # Check if the checkbox is selected
        checkbox_element = driver.find_element(By.ID, "follow-company-checkbox")
        if checkbox_element.is_selected():
            # Click the label to uncheck the box (since checkbox is hidden)
            label_element.click()
            print("Unchecked the 'Follow' checkbox.")
        else:
            print("'Follow' checkbox was already unchecked.")

    except NoSuchElementException as e:
        print(f"Error while handling the 'Follow' checkbox: {e}")
    except TimeoutException as e:
        print(f"'Follow' checkbox not found in time: {e}")
    except Exception as e:
        print(f"Unexpected error while handling the 'Follow' checkbox: {e}")


# Example function to scrape job description using Selenium
def scrape_job_description(driver):
    try:
        # Wait until the job description is present and visible
        job_description_element = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "job-details"))
        )
        job_description = job_description_element.text.strip()
        # print(f"Job Description: {job_description}")
        return job_description

    except Exception as e:
        print(f"Error scraping job description: {e}")
        return None


def get_all_job_cards(driver):
    try:
        # Wait until all job cards are loaded on the page
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located(
                (By.XPATH, "//li[contains(@class, 'jobs-search-results__list-item')]")
            )
        )

        # Grab all the job cards from the list
        job_cards = driver.find_elements(
            By.XPATH, "//li[contains(@class, 'jobs-search-results__list-item')]"
        )

        return job_cards
    except TimeoutException:
        print("Timed out waiting for job cards to load.")
        return []


def click_next_page(driver):
    try:
        # Wait for the "Next" button to be present and enabled
        next_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable(
                (By.XPATH, "//button[contains(@aria-label, 'View next page')]")
            )
        )
        next_button.click()
        print("Navigating to the next page...")
        return True  # Successfully clicked
    except (NoSuchElementException, TimeoutException) as e:
        print("No more pages to navigate or error finding 'Next' button:", e)
        return False  # No more pages


def update_yaml_with_env(yaml_file_path):
    """
    Updates the YAML configuration file with values from the environment variables.

    :param yaml_file_path: Path to the YAML configuration file.
    """

    # Load environment variables from the .env file
    load_dotenv()

    # Load the existing YAML configuration file
    try:
        with open(yaml_file_path, "r") as yaml_file:
            config_data = yaml.safe_load(yaml_file)
    except FileNotFoundError:
        print(f"YAML file {yaml_file_path} not found.")
        return
    except yaml.YAMLError as exc:
        print(f"Error parsing YAML file: {exc}")
        return

    # Access environment variables and update the config data
    updated_data = {
        "first name": os.getenv("FIRST_NAME", config_data.get("first name")),
        "last name": os.getenv("LAST_NAME", config_data.get("last name")),
        "Email address": os.getenv("EMAIL_ADDRESS", config_data.get("Email address")),
        "Mobile phone number": os.getenv(
            "MOBILE_PHONE_NUMBER", config_data.get("Mobile phone number")
        ),
    }

    # Merge updated data with the existing config data
    config_data.update(updated_data)

    # Write the updated config data back to the YAML file
    try:
        with open(yaml_file_path, "w") as yaml_file:
            yaml.dump(config_data, yaml_file)
        print("YAML configuration updated successfully.")
    except Exception as exc:
        print(f"Failed to write updated data to YAML file: {exc}")
