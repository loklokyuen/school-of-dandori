import pandas as pd
import chromadb
from chromadb import EmbeddingFunction, Embeddings, Documents
from chromadb.utils.embedding_functions import DefaultEmbeddingFunction
from fetch_from_firestore import get_all_courses_from_firestore

def ingest_data():
    df = get_all_courses_from_firestore()

    def format_list(item):
        """Helper to handle list fields safely for text and metadata."""
        if isinstance(item, list):
            return ", ".join(item)
        return str(item) if item else ""

    chunks = []
    metadatas = []
    ids = []

    for i, row in df.iterrows():
        skills_str = format_list(row.get('skills', []))
        objectives_str = format_list(row.get('learning_objectives', []))
        materials_str = format_list(row.get('provided_materials', []))

        chunk = f"""
            COURSE: {row['title']}\n
            Class ID: {row['class_id']}\n
            Instructor: {row['instructor']}\n
            Type: {row['course_type']}\n
            Location: {row['location']}\n
            Skills: {skills_str}\n
            Objectives: {objectives_str}\n
            Description: {row['description']}\n
            Provided Materials : {materials_str}\n
            """.strip()
        
        chunks.append(chunk)

        # The Metadata: For filtering
        metadatas.append({
            "class_id": str(row['class_id']),
            "instructor": str(row['instructor']),
            "course_type": str(row['course_type']),
            "location": str(row['location']),
            "cost": float(row['cost']) if row['cost'] else 0.0,
            "skills": skills_str  
        })

        # Use actual class_id as the ID to prevent duplicates
        ids.append(str(i))

    # ChromaDB Operations
    client = chromadb.PersistentClient(path="./chroma_store")
    collection = client.get_or_create_collection(
        name="courses",
        embedding_function=DefaultEmbeddingFunction()
    )


    collection.upsert(
        documents=chunks, 
        metadatas=metadatas, 
        ids=ids
    )
    print(f"Ingested {len(chunks)} courses into ChromaDB")

if __name__ == "__main__":
    ingest_data()