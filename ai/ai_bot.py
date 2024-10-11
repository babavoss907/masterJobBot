# ai/ai_bot.py
import openai
import os
from dotenv import load_dotenv

# Load environment variables (API key from .env)
load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")


# Function to generate cover letter using GPT-3.5
def generate_cover_letter(job_description, resume):
    prompt = f"""
    Write a personalized cover letter for the following job description based on the candidate's resume:
    
    Job Description: {job_description}
    
    Resume: {resume}
    """

    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {
                "role": "system",
                "content": "You are an assistant that writes custom cover letters based on job descriptions and resumes.",
            },
            {"role": "user", "content": prompt},
        ],
        max_tokens=300,
        n=1,
        temperature=0.7,
    )

    return response["choices"][0]["message"]["content"]


# Function to generate an answer for a question based on resume using GPT-3.5
def generate_answer_with_gpt(question, resume):
    prompt = f"""
    You are a job applicant answering questions for a job application based on the following resume:
    
    Resume: {resume}
    
    Answer the following question: {question}
    """

    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {
                "role": "system",
                "content": "You are an assistant answering job-related questions based on the provided resume.",
            },
            {"role": "user", "content": prompt},
        ],
        max_tokens=200,
        n=1,
        temperature=0.7,
    )

    return response["choices"][0]["message"]["content"]
