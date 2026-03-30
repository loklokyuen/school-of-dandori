import streamlit as st
import pandas as pd
from openai import OpenAI
import os
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.getenv("OPENROUTER_API_KEY")
)
# load the csv into a dataframe
df = pd.read_csv("courses.csv")

# build a prompt for the LLM
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
        model="mistralai/mistral-7b-instruct",
        messages=[{"role": "system", "content": system_prompt}] + messages
    )
    return response.choices[0].message.content

#------------ streamlit page -----------------------

st.set_page_config(page_title="Course Advisor", page_icon="🌘")
st.title("🌘 Course Advisor")
st.write("Tell me what you're looking for and I'll help you find the perfect course")

# --- Initialise session state ---
if "messages" not in st.session_state:
    st.session_state.messages = []

# --- Clear conversation button ---
if st.button("Start new conversation"):
    st.session_state.messages = []

# --- Display conversation history ---
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.write(message["content"])

# --- Handle new input ---
if user_input := st.chat_input("What kind of course are you looking for?"):

    # Add and display user message
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.write(user_input)

    # Get and display assistant response
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            system_prompt = build_system_prompt(df)
            response = chat(st.session_state.messages, system_prompt)
            st.write(response)

    # Add assistant response to history
    st.session_state.messages.append({"role": "assistant", "content": response})