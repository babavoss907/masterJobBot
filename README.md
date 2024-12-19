This is a Python-based bot that automates job applications on LinkedIn using Selenium. The bot applies for jobs and leverages OpenAI to auto-fill questions and generate responses based on your resume when required.

## Features

- Automated job application submission on LinkedIn using "Easy Apply."
- Customizable job search filters and auto-form filling using Selenium.
- Integrated with OpenAI to generate answers based on your resume when no answer is provided.
- Handles pagination to apply for jobs across multiple pages.
- Auto-fills job forms based on a YAML configuration file or generates answers with AI if data is missing.

## Prerequisites

To use this bot, ensure you have:

- Python 3.8+ installed on your machine.
- Google Chrome installed and updated to the latest version.

### LinkedIn Credentials

Make sure you have a `.env` file that stores your LinkedIn credentials:

```ini
LINKEDIN_USERNAME=your_linked_in_username
LINKEDIN_PASSWORD=your_linked_in_password
```

git clone https://github.com/yourusername/job-application-bot.git

cd job-application-bot

pip install pipenv
pipenv install

pip install -r requirements.txt
