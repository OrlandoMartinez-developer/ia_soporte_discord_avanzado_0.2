
from sentence_transformers import SentenceTransformer
import chromadb
import os

model = SentenceTransformer("all-MiniLM-L6-v2")
chroma = chromadb.Client()
collection = chroma.get_or_create_collection("docs")

def load_docs():
    all_texts = []
    for fname in os.listdir("docs"):
        if fname.endswith(".txt"):
            with open(f"docs/{fname}", "r", encoding="utf-8") as f:
                all_texts.append(f.read())
    return all_texts

texts = load_docs()
embeddings = model.encode(texts)

for i, text in enumerate(texts):
    collection.add(documents=[text], ids=[str(i)], embeddings=[embeddings[i]])
