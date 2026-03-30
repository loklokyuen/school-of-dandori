import pandas as pd
import chromadb
from chromadb import EmbeddingFunction, Embeddings, Documents
from chromadb.utils.embedding_functions import DefaultEmbeddingFunction

df = pd.read_csv("courses.csv")

# Combine fields into a rich text chunk per course
def make_chunk(row):
    return f"""
Title: {row['title']}
Instructor: {row['instructor']}
Course Type: {row['course_type']}
Location: {row['location']}
Cost: £{row['cost']}
Skills: {row['skills']}
Objectives: {row['learning_objectives']}
Description: {row['description']}
Class ID: {row['class_id']}
""".strip()

chunks = [make_chunk(row) for _, row in df.iterrows()]
ids = [str(i) for i in range(len(df))]

client = chromadb.PersistentClient(path="./chroma_store")
collection = client.get_or_create_collection(
    name="courses",
    embedding_function=DefaultEmbeddingFunction()
)

collection.add(documents=chunks, ids=ids)
print(f"Ingested {len(chunks)} courses into ChromaDB")