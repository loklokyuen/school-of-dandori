from openai import OpenAI
import pandas as pd
import os
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.getenv("OPENROUTER_API_KEY")
)
# load the csv into a dataframe
df = pd.read_csv("courses.csv")


#build a prompt for the LLM
def build_system_prompt(df):
    course_list = ""
    for _, row in df.iterrows():
        course_list += f"- ID: {row['class_id']} | {row['title']} | {row['location']} | {row['cost']} | Type: {row['course_type']} | Skills: {row['skills']}\n"

    return f"""
    You are a friendly and whimsical course advisor for the School of Dandori, 
    an adult education platform offering playful and creative evening and weekend classes.

    Your job is to help users find the right course through friendly conversation. 
    Ask follow up questions to understand what they're looking for — such as location, 
    budget, interests, or what kind of experience they want.

    When you have enough information, recommend 1-3 courses from the list below.
    Always mention the Class ID so users can book.
    Never make up courses that aren't in the list.

    Available courses:
    {course_list}
    """

def chat(messages, system_prompt):
    response = client.chat.completions.create(
        model="anthropic/claude-haiku-4-5",
        messages=[{"role": "system", "content": system_prompt}] + messages
    )
    return response.choices[0].message.content


# --- Simple test loop ---
system_prompt = build_system_prompt(df)
messages = []

print("School of Dandori Course Advisor (type 'quit' to exit)\n")

while True:
    user_input = input("You: ")
    
    if user_input.lower() == "quit":
        break

    messages.append({"role": "user", "content": user_input})
    response = chat(messages, system_prompt)
    messages.append({"role": "assistant", "content": response})
    
    print(f"\nAdvisor: {response}\n")