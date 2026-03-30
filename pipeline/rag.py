import chromadb
from chromadb.utils.embedding_functions import DefaultEmbeddingFunction
from openai import OpenAI
from dotenv import load_dotenv
import os

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

def ask(question: str, n_results: int = 5) -> str:
    # 1. Retrieve relevant courses
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