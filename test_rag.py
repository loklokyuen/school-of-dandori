# test_rag.py
from pipeline.rag import ask

response = ask("I want a relaxing creative course in the Scottish Highlands")
print(response)