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
    Based on the following resume information, provide a concise and direct answer to the question below. If the question is asking for years of experience and it's not provided in the resume, return a random number between 2 and 3. The response should not include any explanations or estimates—just or punctuation. The random number response should only be the number "2" or the number "3". If a question is asking implicity for a "yes" or "no" only return 1 of those.

    
    Resume Information:
    {resume_info}
    
    Question:
    {question}
    
    Answer:
    """

    response = openai.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {
                "role": "system",
                "content": "You are an AI that answers job application as the person who is applying for the job.",
            },
            {"role": "user", "content": prompt},
        ],
    )
    response_message = response.choices[0].message.content
    return response_message
