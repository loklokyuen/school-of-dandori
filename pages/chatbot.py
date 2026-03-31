import streamlit as st
import pandas as pd
import chromadb
from chromadb.utils.embedding_functions import DefaultEmbeddingFunction
import json
from openai import OpenAI
import os
from dotenv import load_dotenv
from pipeline.ingest import sync_all

load_dotenv()
# --- Configuration ---
DISCOVERY_QUESTIONS = [
    "Before we dive in, which location works best for you? (Brighton, Bath, or Windsor?)",
    "And what are you most interested in? (e.g., Crafting, Yoga, Knitting, or something else?)",
]

# --- Initialize Session State ---
if "question_idx" not in st.session_state:
    st.session_state.question_idx = 0
if "discovery_answers" not in st.session_state:
    st.session_state.discovery_answers = {}
if "discovery_complete" not in st.session_state:
    st.session_state.discovery_complete = False

load_dotenv()

with st.sidebar:
    if st.button("🔄 Sync with Firestore"):
        with st.spinner("Syncing latest courses..."):
            db_info = sync_all()
            st.success(f"Database Synced")

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
df = pd.read_csv("./data/courses.csv")

REGION_MAP = {
    "south west": ["bristol", "bath", "exeter", "gloucester", "plymouth", "cheltenham"],
    "london": ["london", "greater london", "central london", "hackney", "camden"],
    "south east": ["brighton", "oxford", "reading", "southampton", "canterbury"],
    "midlands": ["birmingham", "coventry", "leicester", "nottingham"],
    "north west": ["manchester", "liverpool", "salford"]
}

def validate_location(user_input):
    """
    Returns (is_valid, matched_locations, message)
    """
    user_input_clean = user_input.strip().lower()
    
    # 1. Direct Match (Exact city/location name)
    # Check if any available location (lowercase) matches user input
    unique_locations = df['location'].str.lower().unique().tolist()
    matched_cities = [loc for loc in unique_locations if loc in user_input_clean]
    if matched_cities:
        official_name = matched_cities[0].title() 
        return True, [official_name], f"Perfect! We have several courses in {official_name.title()}."

    # 2. Region Match
    for region, cities in REGION_MAP.items():
        if region in user_input_clean:
            # Filter unique_locations to find which ones belong to this region
            matches = [loc.title() for loc in unique_locations if loc in cities]
            if matches:
                return True, matches, f"Great! In the {region.title()}, we have courses in: {', '.join(matches)}."
            else:
                return False, [], f"We know the {region.title()}, but we don't have any classes listed there right now."
    # 3. Outside UK / Invalid
    return False, [], "I'm sorry, we currently only offer courses within specific UK regions. We don't have anything available in that area right now."

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
    print(filters)
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
    answers = st.session_state.discovery_answers
    system = f"""You are a friendly course advisor for the School of Dandori,
                an adult education platform offering playful and creative evening and weekend classes.
                Your job is to help users find the right course through friendly conversation.
                Ask follow up questions to understand what they're looking for — such as location,
                budget, interests, or what kind of experience they want.
                Use only the course information provided to make recommendations.
                If no courses match, say so honestly. Always mention the Class ID when recommending a course.
                Never make up courses that aren't in the provided list.
                The user has already provided this context:
                - Preferred Location: {answers.get('location')}
                - Interests: {answers.get('interests')}
                """

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
    st.session_state.messages = [{"role": "assistant", "content": DISCOVERY_QUESTIONS[0]}]

# --- Clear conversation button ---
if st.button("Start new conversation"):
    st.session_state.messages = [{"role": "assistant", "content": DISCOVERY_QUESTIONS[0]}]
    st.session_state.question_idx = 0
    st.session_state.discovery_answers = {}
    st.session_state.discovery_complete = False
    st.rerun()


# --- Display conversation history ---
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.write(message["content"])

# --- Handle Input ---
if user_input := st.chat_input("Type here..."):
    
    # 1. ADD USER MESSAGE TO UI
    st.session_state.messages.append({"role": "user", "content": user_input})

    # 2. ARE WE STILL IN DISCOVERY?
    if not st.session_state.discovery_complete:
        # Store the answer to the PREVIOUS question
        current_q_idx = st.session_state.question_idx
        if current_q_idx == 0: 
            is_valid, matches, feedback = validate_location(user_input)
            
            if is_valid:
                # Save the specific locations found for filtering later
                st.session_state.discovery_answers['location'] = matches
                # st.session_state.messages.append({"role": "assistant", "content": feedback})
                st.session_state.question_idx += 1 
            else:
                st.session_state.messages.append({"role": "assistant", "content": feedback + " Could you try a different location?"})
                st.rerun()
        elif current_q_idx < len(DISCOVERY_QUESTIONS):
            key_map = ["location", "interests"]
            key = key_map[current_q_idx]
            st.session_state.discovery_answers[key] = user_input
            st.session_state.question_idx += 1

        # --- PHASE 3: CHECK IF WE JUST FINISHED ---
        if st.session_state.question_idx < len(DISCOVERY_QUESTIONS):
            next_q = DISCOVERY_QUESTIONS[st.session_state.question_idx]
            st.session_state.messages.append({"role": "assistant", "content": feedback + " " + next_q})
        else:
            st.session_state.discovery_complete = True
            st.session_state.messages.append({
                "role": "assistant", 
                "content": "Perfect! Searching for the best courses now..."
            })
            relevant_courses = get_relevant_courses("Location: " + str(st.session_state.discovery_answers['location']).title() + user_input)
            response = chat(st.session_state.messages, relevant_courses)
            st.session_state.messages.append({"role": "assistant", "content": response})
    
    else:
        # 3. NORMAL RAG CHAT MODE
        # Use the discovery_answers to help filter your search!
        relevant_courses = get_relevant_courses(user_input)
        response = chat(st.session_state.messages, relevant_courses)
        st.session_state.messages.append({"role": "assistant", "content": response})
        with st.chat_message("assistant"):
            display_response_with_cards(response)

    st.rerun()