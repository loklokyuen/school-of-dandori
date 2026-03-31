import chromadb
from chromadb.utils.embedding_functions import DefaultEmbeddingFunction
from openai import OpenAI
from dotenv import load_dotenv
import os
import pandas as pd

df = pd.read_csv("courses.csv")

load_dotenv()

client = chromadb.PersistentClient(path="./chroma_store")
collection = client.get_or_create_collection(
    name="courses",
    embedding_function=DefaultEmbeddingFunction()
)

openrouter = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.getenv("OPENROUTER_API_KEY")
)

def ask(question: str, n_results: int = 10) -> str:
    # 1. Retrieve relevant courses
    results = collection.query(query_texts=[question], n_results=10)
    
    # Check if a location is mentioned and pre-filter
    location_filter = None
    for location in df["location"].unique():
        if location.lower() in question.lower():
            location_filter = location
            break
    
    if location_filter:
        # Use CSV filter instead of ChromaDB for location queries
        filtered = df[df["location"].str.lower() == location_filter.lower()]
        context = "\n\n---\n\n".join([
            f"Title: {row['title']}\nInstructor: {row['instructor']}\nCourse Type: {row['course_type']}\nLocation: {row['location']}\nCost: £{row['cost']}\nSkills: {row['skills']}\nDescription: {row['description']}\nClass ID: {row['class_id']}"
            for _, row in filtered.iterrows()
        ])
    else:
        # Fall back to ChromaDB for semantic queries
        results = collection.query(query_texts=[question], n_results=n_results)
        context = "\n\n---\n\n".join(results["documents"][0])

    # 2. Build prompt
    system = """You are a friendly course advisor for School of Dandori.
Use only the course information provided to answer the student's question.
If no courses match, say so honestly. Always mention the Class ID when recommending a course."""

    prompt = f"""Here are the most relevant courses:\n\n{context}\n\nStudent question: {question}"""

    # 3. Call Mistral via OpenRouter
    response = openrouter.chat.completions.create(
        model="openrouter/free",
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": prompt}
        ]
    )

    return response.choices[0].message.content