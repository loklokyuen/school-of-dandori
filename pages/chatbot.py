import streamlit as st
import pandas as pd
import chromadb
from chromadb.utils.embedding_functions import DefaultEmbeddingFunction
import json
from openai import OpenAI
import os
from dotenv import load_dotenv

load_dotenv()

# --- Clients ---
chroma_client = chromadb.PersistentClient(path="./chroma_store")
collection = chroma_client.get_or_create_collection(
    name="courses",
    embedding_function=DefaultEmbeddingFunction()
)

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=st.secrets.get("OPENROUTER_API_KEY") or os.getenv("OPENROUTER_API_KEY")
)
# load the csv into a dataframe
df = pd.read_csv("courses.csv")

# initial prompt to the llm to extract metadata from the users inital input
def extract_filters(user_message):
    response = client.chat.completions.create(
        model="mistralai/mistral-small-2603",
        messages=[{
            "role": "user",
            "content": f"""You are helping to identify search filters from messages from users looking for courses in the UK.

            Extract any of the following from the message:
            - location: a UK town, city, or region
            - max_cost: a maximum budget as a number only (no £ symbol)
            - course_type: the type of course (e.g. Mindfulness, Crafts, Nature)
            - skills: any skills the user mentions (e.g. painting, pottery, yoga)

            Return ONLY a JSON object with these fields. Use null if not mentioned.

            Examples:
            "I want something in Windsor under £50" -> {{"location": "Windsor", "max_cost": 50, "course_type": null, "skills": null}}
            "a mindfulness class" -> {{"location": null, "max_cost": null, "course_type": "Mindfulness", "skills": null}}
            "something creative" -> {{"location": null, "max_cost": null, "course_type": null, "skills": "creative"}}
            "yoga near Bath for under £40" -> {{"location": "Bath", "max_cost": 40, "course_type": null, "skills": "yoga"}}

            Message: {user_message}"""
        }]
    )

    try:
        raw = response.choices[0].message.content.strip()
        # strip markdown code fences if the model wraps the response
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        return json.loads(raw.strip())
    except:
        return {"location": None, "max_cost": None, "course_type": None, "skills": None}

# --- RAG function ---
def get_relevant_courses(question, n_results=15):
    filters = extract_filters(question)

    # build chromadb where clause from extracted filters
    where_conditions = []

    if filters.get("location"):
        where_conditions.append({"location": {"$eq": filters["location"].title()}})

    if filters.get("max_cost"):
        where_conditions.append({"cost": {"$lte": filters["max_cost"]}})

    if filters.get("course_type"):
        where_conditions.append({"course_type": {"$eq": filters["course_type"]}})

    # apply filters if any were found
    if where_conditions:
        where = {"$and": where_conditions} if len(where_conditions) > 1 else where_conditions[0]
        results = collection.query(
            query_texts=[question],
            n_results=n_results,
            where=where
        )
    else:
        results = collection.query(
            query_texts=[question],
            n_results=n_results
        )

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