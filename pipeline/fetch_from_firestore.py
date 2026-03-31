from google.cloud import firestore
from dotenv import load_dotenv
import streamlit as st
import pandas as pd
import os
import json
import tempfile

load_dotenv()

def get_db():
    if "GOOGLE_CREDENTIALS" in st.secrets:
        # Running on Streamlit Cloud — load from secrets
        credentials_dict = dict(st.secrets["GOOGLE_CREDENTIALS"])
        credentials_dict["private_key"] = credentials_dict["private_key"].replace("\\n", "\n")
        
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(credentials_dict, f)
            os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = f.name
    
    return firestore.Client(project="buoyant-world-491810-n6")

#@st.cache_data(ttl=300) 
def read_course_from_firestore(class_id, title):
    """
    Reads a single course document from the 'courses' collection in Firestore.
    Args:
        class_id: The ID of the course document to read.
    Returns:
        A dictionary containing the course data if found, otherwise None.
    """
    db = get_db()
    doc_ref = db.collection("courses").document(class_id + " " + title)
    doc = doc_ref.get()

    if doc.exists:
        df = pd.DataFrame(doc)
        return df
    else:
        print(f"No document found with class_id: {class_id}")
        return None

def get_nb_courses():
    db = get_db()
    firestore_doc_count = 0
    collection_ref = db.collection('courses')

    for doc in collection_ref.stream():
        firestore_doc_count += 1
    print(f"Number of documents in Firestore 'courses' collection: {firestore_doc_count}")

#@st.cache_data(ttl=300) 
def get_all_courses_from_firestore():
    """
    Retrieves all course documents from the 'courses' collection in Firestore.
    Returns:
        A list of dictionaries, where each dictionary represents a course.
    """
    db = get_db()
    courses_ref = db.collection("courses")
    all_courses = []

    # Get all documents in the collection
    docs = courses_ref.stream()

    for doc in docs:
        course_data = doc.to_dict()
        course_data['id'] = doc.id
        all_courses.append(course_data)
    if all_courses:
        df = pd.DataFrame(all_courses)
        return df
    else:
        print("No documents found in the 'courses' collection.")
        return pd.DataFrame()


