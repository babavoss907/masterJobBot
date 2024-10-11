# ai/ai_bot.py
import openai
import os
from dotenv import load_dotenv

# Load environment variables (API key from .env)
load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

# Load the resume information from the text file
with open("resources/resume_prompt.txt", "r") as file:
    resume_info = file.read()


# Function to generate cover letter using GPT-3.5
def generate_cover_letter(job_description):
    prompt = f"""
    Based on the following resume information, generate a custom cover letter for the job described below:
    
    Resume Information:
    {resume_info}
    
    Job Description:
    {job_description}
    
    Cover Letter:
    """

    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {
                "role": "system",
                "content": "You are an AI that writes professional cover letters.",
            },
            {"role": "user", "content": prompt},
        ],
    )

    return response["choices"][0]["message"]["content"]


# Function to generate an answer for a question based on resume using GPT-3.5
def generate_answer_for_question(question):
    prompt = f"""
    Based on the following resume information, provide a detailed answer for the question below if no answer provided make a best guess. If the question is asking for a number of years for a specific technoloy that isnt provided randomize between 2 and 3.:
    
    Resume Information:
    {resume_info}
    
    Question:
    {question}
    
    Answer:
    """

    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {
                "role": "system",
                "content": "You are an AI that answers job application questions.",
            },
            {"role": "user", "content": prompt},
        ],
    )

    return response["choices"][0]["message"]["content"]
