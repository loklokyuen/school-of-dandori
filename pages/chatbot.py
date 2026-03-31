import streamlit as st
import pandas as pd
import chromadb
from chromadb.utils.embedding_functions import DefaultEmbeddingFunction
from openai import OpenAI
import os
from dotenv import load_dotenv

load_dotenv()

# --- Clients ---
chroma_client = chromadb.PersistentClient(path="./pipeline/chroma_store")
collection = chroma_client.get_or_create_collection(
    name="courses",
    embedding_function=DefaultEmbeddingFunction()
)

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.getenv("OPENROUTER_API_KEY")
)
# load the csv into a dataframe
df = pd.read_csv("courses.csv")

# --- RAG function ---
def get_relevant_courses(question, n_results=15):
    results = collection.query(query_texts=[question], n_results=n_results)
    return "\n\n---\n\n".join(results["documents"][0])

# --- Chat function ---
def chat(messages, relevant_courses):
    system = """You are a friendly course advisor for the School of Dandori,
                an adult education platform offering playful and creative evening and weekend classes.
                Your job is to help users find the right course through friendly conversation.
                Ask follow up questions to understand what they're looking for — such as location,
                budget, interests, or what kind of experience they want.
                Use only the course information provided to make recommendations.
                If no courses match, say so honestly. Always mention the Class ID when recommending a course.
                Never make up courses that aren't in the provided list."""

    # inject the relevant courses into the last user message
    augmented_messages = messages[:-1] + [{
        "role": "user",
        "content": f"Relevant courses:\n\n{relevant_courses}\n\nStudent message: {messages[-1]['content']}"
    }]

    response = client.chat.completions.create(
        model="mistralai/mistral-small-2603",
        messages=[{"role": "system", "content": system}] + augmented_messages
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

    relevant_courses = get_relevant_courses(user_input)
    
    # debug here - before anything else
    st.write("DEBUG - relevant courses:")
    st.write(relevant_courses)

    # Add and display user message
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.write(user_input)

    # Get relevant courses from ChromaDB
    relevant_courses = get_relevant_courses(user_input)

    # Get and display assistant response
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            response = chat(st.session_state.messages, relevant_courses)
            st.write(response)

    # Add assistant response to history
    st.session_state.messages.append({"role": "assistant", "content": response})