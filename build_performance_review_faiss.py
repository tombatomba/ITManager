import os
import numpy as np
import faiss
from openai import OpenAI
from config import Config

# inicijalizacija OpenAI client
client = OpenAI(api_key=Config.OPENAI_API_KEY)

# folder sa knowledge fajlovima
KNOWLEDGE_DIR = "knowledge/companyinfo"

# gde ćemo sačuvati FAISS indeks i metadata
os.makedirs("faiss", exist_ok=True)
INDEX_PATH = "faiss/company_info.index"
META_PATH = "faiss/company_info_meta.npy"

texts = []
metadata = []

# 1️⃣ Učitaj fajlove iz foldera
for filename in os.listdir(KNOWLEDGE_DIR):
    if filename.endswith(".md"):
        path = os.path.join(KNOWLEDGE_DIR, filename)
        with open(path, "r", encoding="utf-8") as f:
            content = f.read().strip()
            if content:  # filtriraj prazne fajlove
                texts.append(content)
                print(filename)
                metadata.append({
                    "file": filename,
                    "topic": "company_info",
                    "content": content   
                })

if not texts:
    raise ValueError("No valid knowledge files found in folder: " + KNOWLEDGE_DIR)

print(f"Found {len(texts)} valid knowledge chunks")

# 2️⃣ Kreiraj embeddings za sve fajlove
response = client.embeddings.create(
    model="text-embedding-3-large",
    input=texts
)


if hasattr(response, "usage"):
    print(f"Total tokens used for embeddings: {response.usage.total_tokens}")
else:
    print("Token usage info not available in this SDK version.")

vectors = [e.embedding for e in response.data]
vectors = np.array(vectors).astype("float32")

# 3️⃣ Kreiraj FAISS indeks
dimension = vectors.shape[1]
index = faiss.IndexFlatL2(dimension)
index.add(vectors)

# 4️⃣ Sačuvaj indeks i metadata
faiss.write_index(index, INDEX_PATH)
np.save(META_PATH, metadata)

print(f"FAISS index kreiran sa {index.ntotal} knowledge chunk-ova")
print(f"Index path: {INDEX_PATH}")
print(f"Metadata path: {META_PATH}")