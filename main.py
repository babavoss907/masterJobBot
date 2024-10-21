import os

from dotenv import load_dotenv

# scripts / job_application_bot.py
from scripts.job_application_bot import (
    load_config,
    linkedin_login,
    apply_to_jobs,
    setup_driver,
    update_yaml_with_env,
)

load_dotenv("resources/.env")
LINKEDIN_USERNAME = os.getenv("LINKEDIN_USERNAME")
LINKEDIN_PASSWORD = os.getenv("LINKEDIN_PASSWORD")
config_path = "resources/config.yaml"


if __name__ == "__main__":
    # Load the config file for answers to questions
    config = load_config()
    update_yaml_with_env(config_path)
    # Set up the Selenium WebDriver
    driver = setup_driver()  # Ensure setup_driver function is properly set up
    linkedin_login(driver, LINKEDIN_USERNAME, LINKEDIN_PASSWORD)

    # Wait for manual login
    input("Please manually log in and apply filters. Press Enter to continue...")

    # Try to apply to jobs using Easy Apply
    try:
        apply_to_jobs(driver, config)
    finally:
        # Always close the driver at the end
        driver.quit()
