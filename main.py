import os

from dotenv import load_dotenv

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
    config = load_config()
    update_yaml_with_env(config_path)
    driver = setup_driver()
    linkedin_login(driver, LINKEDIN_USERNAME, LINKEDIN_PASSWORD)

    input("Please manually log in and apply filters. Press Enter to continue...")

    try:
        apply_to_jobs(driver, config)
    finally:
        driver.quit()
