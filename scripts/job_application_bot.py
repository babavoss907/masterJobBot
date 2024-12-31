import os
import time
import yaml
import logging

from dotenv import load_dotenv
from webdriver_manager.chrome import ChromeDriverManager

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import ElementClickInterceptedException
from selenium.common.exceptions import (
    NoSuchElementException,
    TimeoutException,
    StaleElementReferenceException,
    ElementNotInteractableException,
)

# ai automation not implemented yet
from ai.ai_bot import generate_cover_letter, generate_answer_for_question

load_dotenv("resources/.env")
LINKEDIN_USERNAME = os.getenv("LINKEDIN_USERNAME")
LINKEDIN_PASSWORD = os.getenv("LINKEDIN_PASSWORD")

config_path = "resources/config.yaml"


def setup_driver():
    chrome_options = Options()

    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")

    chrome_options.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    )

    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option("useAutomationExtension", False)

    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)

    driver.execute_script(
        "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
    )

    return driver


def linkedin_login(driver, LINKEDIN_USERNAME, LINKEDIN_PASSWORD):
    driver.get("https://www.linkedin.com/login")

    try:
        username_field = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "username"))
        )
        print("Username field found!")

        password_field = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "password"))
        )
        print("Password field found!")

        login_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, '//button[@type="submit"]'))
        )
        print("Login button found!")

        username_field.send_keys(LINKEDIN_USERNAME)
        password_field.send_keys(LINKEDIN_PASSWORD)

        login_button.click()
        print("Login form submitted!")

        WebDriverWait(driver, 15).until(EC.url_contains("/feed"))
        print("Logged in successfully!")

    except Exception as e:
        print(f"Login failed: {e}")


def load_config():
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
        while True:
            print("Scrolling down to load job listings...")
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)

            jobs = get_all_job_cards(driver)

            for index, job in enumerate(jobs):
                try:
                    print(f"Clicking job card {index+1}")
                    driver.execute_script("arguments[0].scrollIntoView(true);", job)
                    WebDriverWait(driver, 3).until(
                        EC.element_to_be_clickable(job)
                    ).click()
                    time.sleep(2)

                    try:
                        job_description = scrape_job_description(driver)

                        easy_apply_button = WebDriverWait(driver, 5).until(
                            EC.element_to_be_clickable(
                                (By.CLASS_NAME, "jobs-apply-button")
                            )
                        )
                        driver.execute_script(
                            "arguments[0].click();", easy_apply_button
                        )
                        print("Easy Apply button clicked!")

                        fill_application_form(driver, config)

                    except Exception:
                        print(
                            f"No Easy Apply button found for job {index+1}. Skipping to next job."
                        )

                except Exception as e:
                    print(f"Error clicking job card {index+1}: {e}")
                    continue

            if not click_next_page(driver):
                break

    except Exception as e:
        print(f"Error while processing jobs: {e}")


logging.basicConfig(
    filename="unanswered_questions.log",
    level=logging.INFO,
    format="%(message)s",
)


def fill_application_form(driver, answers):
    try:
        while True:
            fill_form_fields(driver, answers)

            try:
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
                    print("Click intercepted, retrying without scrolling...")
                    driver.execute_script("arguments[0].click();", next_button)

                time.sleep(2)
                WebDriverWait(driver, 15).until(
                    EC.presence_of_element_located(
                        (By.XPATH, "//input | //select | //textarea")
                    )
                )

            except TimeoutException:
                try:
                    review_button = WebDriverWait(driver, 10).until(
                        EC.element_to_be_clickable(
                            (
                                By.XPATH,
                                '//button[contains(@aria-label, "Review your application") or contains(aria-label, "Review")]',
                            )
                        )
                    )
                    driver.execute_script(
                        "arguments[0].scrollIntoView(true);", review_button
                    )
                    try:
                        review_button.click()
                        print("Clicked on 'Review' button.")
                    except ElementClickInterceptedException:
                        print("Click intercepted, retrying without scrolling...")
                        driver.execute_script("arguments[0].click();", review_button)

                    time.sleep(2)

                    try:
                        handle_follow_checkbox(driver)
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
    new_answers = {}

    def get_label_question_text(label):
        """Extract question text from a label or fieldset, and clean it."""
        try:
            label_text = label.text.strip()
            if label_text:
                return label_text

            span_element = label.find_element(By.XPATH, ".//span")
            if span_element:
                return span_element.text.strip()

            fieldset = label.find_element(By.XPATH, "./ancestor::fieldset")
            if fieldset:
                legend = fieldset.find_element(By.XPATH, ".//legend/span")
                return legend.text.strip() if legend else ""

            return label.text.strip()

        except Exception as e:
            print(f"Error extracting question text from label: {e}")
            return label.text.strip() if label.text else ""

    def handle_resume_prefilled():
        """Skip resume selection if it's already prefilled."""
        try:
            resume_section = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH, "//h3[text()='Resume']"))
            )

            selected_resume = resume_section.find_element(
                By.XPATH,
                "//div[contains(@class, 'jobs-document-upload-redesign-card__container--selected')]",
            )
            if selected_resume:
                resume_name = selected_resume.find_element(
                    By.XPATH, ".//h3"
                ).text.strip()
                print(
                    f"Resume '{resume_name}' is already selected. Skipping resume selection."
                )
                return True
            else:
                print("No preselected resume found. Handling upload if needed.")
                return False

        except Exception as e:
            print(f"Error checking resume selection: {e}")
            return False

    def get_question_text_from_fieldset(fieldset):
        """Extract question text from the legend inside a fieldset."""
        try:
            legend = fieldset.find_element(By.TAG_NAME, "legend")
            question_text = legend.text.strip()
            return question_text
        except Exception as e:
            print(f"Error extracting question text from fieldset: {e}")
            return ""

    def handle_radio_buttons(fieldset, question_text, config):
        """Handle radio button inputs inside a fieldset."""
        try:
            question_text = get_question_text_from_fieldset(fieldset)

            if not question_text:
                return

            cleaned_question_text = question_text.split("\n")[0].strip()
            cleaned_question_text = cleaned_question_text.replace(
                "Required", ""
            ).strip()

            normalized_question_text = cleaned_question_text.lower()

            print(f"Cleaned question text: '{cleaned_question_text}'")

            config_keys = {key.strip().lower(): key for key in config.keys()}

            if normalized_question_text in config_keys:
                answer = config[config_keys[normalized_question_text]]
            else:
                answer = None

            if not answer:
                answer = input(
                    f"Please provide an answer for '{cleaned_question_text}' (Yes/No): "
                )
                new_answers[cleaned_question_text] = answer

            radio_buttons = fieldset.find_elements(By.XPATH, ".//input[@type='radio']")

            for radio_button in radio_buttons:
                label = radio_button.find_element(
                    By.XPATH, "./following-sibling::label"
                ).text.strip()
                if label.lower() == answer.lower():
                    try:
                        label_element = radio_button.find_element(
                            By.XPATH, "./following-sibling::label"
                        )
                        label_element.click()
                        print(f"Selected '{label}' for: {cleaned_question_text}")
                        return
                    except Exception as e:
                        print(
                            f"Error selecting '{label}' for question '{cleaned_question_text}': {e}"
                        )

        except Exception as e:
            print(f"Error handling radio buttons for question '{question_text}': {e}")

    def handle_select_dropdown(input_element, question_text, config):
        """Handle select dropdown inputs."""
        select = Select(input_element)
        current_selection = select.first_selected_option.text.strip()

        if current_selection == "Select an option":
            answer = config.get(question_text)

            if not answer:
                answer = input(f"Please provide an answer for '{question_text}': ")
                if answer:
                    new_answers[question_text] = answer
                    print(f"AI-generated answer for: {question_text}")

            try:
                select.select_by_visible_text(answer)
                print(f"Selected option for: {question_text}")
            except Exception as e:
                print(f"Error selecting option for '{question_text}': {e}")
        else:
            print(
                f"Skipping {question_text}, already filled with value: {current_selection}"
            )

    def handle_text_input(input_element, question_text, config):
        """Handle text input and textarea fields."""
        if "resume" in question_text.lower():
            print(f"Skipping resume-related field: {question_text}")
            return

        existing_value = input_element.get_attribute("value")
        if existing_value and existing_value.lower() != "select an option":
            print(
                f"Skipping {question_text}, already filled with value: {existing_value}"
            )
        else:
            answer = config.get(question_text)

            if not answer:
                answer = input(f"Please provide an answer for '{question_text}': ")
                if answer:
                    new_answers[question_text] = answer
                    print(f"AI-generated answer for: {question_text}")

            input_element.send_keys(answer)
            print(f"Filled answer for: {question_text}")

    def handle_checkbox(input_element, question_text, config):
        """Handle checkbox inputs."""
        is_checked = input_element.is_selected()
        answer = config.get(question_text)

        if not answer:
            answer = input(f"Please provide an answer for '{question_text}': ")
            if answer:
                new_answers[question_text] = answer
                print(f"AI-generated answer for: {question_text}")

        if answer.lower() == "yes" and not is_checked:
            input_element.click()
        elif answer.lower() == "no" and is_checked:
            input_element.click()

    try:
        form = driver.find_element(By.XPATH, "//form")
        labels = form.find_elements(
            By.XPATH, ".//label[not(contains(@class, 'visually-hidden'))]"
        )

        for label in labels:
            question_text = get_label_question_text(label)

            if not question_text or "Search" in question_text:
                continue

            if "Resume" in question_text:
                if handle_resume_prefilled():
                    continue

            try:
                try:
                    fieldset = label.find_element(By.XPATH, "./ancestor::fieldset")
                    handle_radio_buttons(fieldset, question_text, config)
                    continue
                except NoSuchElementException:
                    input_element = label.find_element(
                        By.XPATH,
                        "./following-sibling::input | ./following-sibling::select | ./following-sibling::textarea | ./following-sibling::div//input | ./following-sibling::div//select | ./following-sibling::div//textarea",
                    )

                input_type = input_element.get_attribute("type")

                if input_type == "checkbox":
                    handle_checkbox(input_element, question_text, config)
                elif input_element.tag_name == "select":
                    handle_select_dropdown(input_element, question_text, config)
                elif input_element.tag_name in ["input", "textarea"]:
                    handle_text_input(input_element, question_text, config)
                else:
                    print(f"Unknown field type for {question_text}, skipping.")

            except Exception as e:
                print(f"Error handling field '{question_text}': {e}")

        print("Application form filled out.")

        if len(new_answers) > 0:
            update_config_with_unanswered_questions(config_path, new_answers)

    except Exception as e:
        print(f"Error filling out the application form: {e}")


def close_popup_if_present(driver, retries=3):
    for attempt in range(retries):
        try:
            close_button = WebDriverWait(driver, 5).until(
                EC.presence_of_element_located(
                    (By.XPATH, "//button[@aria-label='Dismiss']")
                )
            )

            if close_button.is_displayed() and close_button.is_enabled():
                try:
                    driver.execute_script(
                        "arguments[0].scrollIntoView(true);", close_button
                    )

                    time.sleep(1)

                    close_button.click()
                    print("Popup closed by clicking 'Dismiss'.")
                    return True

                except ElementClickInterceptedException:
                    print("Click intercepted, retrying with JavaScript...")
                    driver.execute_script("arguments[0].click();", close_button)
                    return True

            else:
                print(
                    f"Close button is present but not interactable on attempt {attempt+1}. Retrying..."
                )

        except StaleElementReferenceException:
            print(
                f"StaleElementReferenceException encountered on attempt {attempt+1}, retrying..."
            )
        except TimeoutException:
            print("No popup found or no close button available.")
            return False
        except ElementNotInteractableException:
            print(f"Element not interactable on attempt {attempt+1}, retrying...")
            time.sleep(2)
        except Exception as e:
            print(f"Unexpected error while handling the pop-up: {e}")
            return False
    print("Failed to close the popup after retries.")
    return False


def handle_follow_checkbox(driver):
    try:
        label_element = WebDriverWait(driver, 15).until(
            EC.presence_of_element_located(
                (By.XPATH, "//label[@for='follow-company-checkbox']")
            )
        )

        driver.execute_script("arguments[0].scrollIntoView(true);", label_element)

        checkbox_element = driver.find_element(By.ID, "follow-company-checkbox")
        if checkbox_element.is_selected():
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


def scrape_job_description(driver):
    try:
        job_description_element = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "job-details"))
        )
        job_description = job_description_element.text.strip()
        return job_description

    except Exception as e:
        print(f"Error scraping job description: {e}")
        return None


def get_all_job_cards(driver):
    try:
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located(
                (By.XPATH, "//li[contains(@class, 'jobs-search-results__list-item')]")
            )
        )

        job_cards = driver.find_elements(
            By.XPATH, "//li[contains(@class, 'jobs-search-results__list-item')]"
        )

        return job_cards
    except TimeoutException:
        print("Timed out waiting for job cards to load.")
        return []


def click_next_page(driver):
    try:
        next_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable(
                (By.XPATH, "//button[contains(@aria-label, 'View next page')]")
            )
        )
        next_button.click()
        print("Navigating to the next page...")
        return True
    except (NoSuchElementException, TimeoutException) as e:
        print("No more pages to navigate or error finding 'Next' button:", e)
        return False


def update_yaml_with_env(yaml_file_path):
    """
    Updates the YAML configuration file with values from the environment variables.

    :param yaml_file_path: Path to the YAML configuration file.
    """

    load_dotenv()

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

    config_data.update(updated_data)

    try:
        with open(yaml_file_path, "w") as yaml_file:
            yaml.dump(config_data, yaml_file)
        print("YAML configuration updated successfully.")
    except Exception as exc:
        print(f"Failed to write updated data to YAML file: {exc}")


def update_config_with_unanswered_questions(config_path, new_answers):
    try:
        with open(config_path, "r") as file:
            config_data = yaml.safe_load(file)

        config_data.update(new_answers)

        with open(config_path, "w") as file:
            yaml.safe_dump(config_data, file)

        print("Config file successfully updated with new answers.")

    except Exception as e:
        print(f"Failed to update config file: {e}")
