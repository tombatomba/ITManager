import faiss
import numpy as np
from openai import OpenAI
from config import Config

# =========================
# CONFIG
# =========================
FAISS_INDEX_PATH = "faiss/company_info.index"
META_PATH = "faiss/company_info_meta.npy"
TEXTS_PATH = "faiss/company_info_texts.npy"

EMBED_MODEL = "text-embedding-3-large"
CHAT_MODEL = "gpt-4o-mini"

TOP_K = 3
DISTANCE_THRESHOLD = 2.0

client = OpenAI(api_key=Config.OPENAI_API_KEY)

# =========================
# LOAD DATA
# =========================
print("Loading FAISS index and data...")

index = faiss.read_index(FAISS_INDEX_PATH)
metadata = np.load(META_PATH, allow_pickle=True)
texts = np.load(TEXTS_PATH, allow_pickle=True)

print(f"Loaded {index.ntotal} vectors")

# =========================
# TEST QUERY
# =========================
query = "ko je vendor za webshop?"

print("\nUSER QUERY:")
print(query)

# =========================
# EMBEDDING QUERY
# =========================
emb = client.embeddings.create(
    model=EMBED_MODEL,
    input=query
)

query_vector = np.array([emb.data[0].embedding]).astype("float32")

# =========================
# FAISS SEARCH
# =========================
D, I = index.search(query_vector, TOP_K)

print("\nFAISS RESULTS:")
context_chunks = []

for rank, idx in enumerate(I[0]):
    distance = D[0][rank]
    source = metadata[idx]["source"]

    print(f"\n#{rank+1}")
    print("Distance:", distance)
    print("Source:", source)

    if distance <= DISTANCE_THRESHOLD:
        context_chunks.append(texts[idx])

# =========================
# CONTEXT DECISION
# =========================
if not context_chunks:
    print("\n⚠️ FAISS match too weak — skipping context")
    context = ""
else:
    context = "\n\n---\n\n".join(context_chunks)

# =========================
# BUILD PROMPT
# =========================
prompt = f"""
You are an internal IT finance assistant.

Use ONLY the following internal context.
If the answer is not present, say:
"I do not have enough internal information."

CONTEXT:
{context}

QUESTION:
{query}
"""

print("\n================ PROMPT SENT TO LLM ================")
print(prompt)
print("====================================================")

# =========================
# CALL OPENAI
# =========================
response = client.chat.completions.create(
    model=CHAT_MODEL,
    messages=[
        {"role": "user", "content": prompt}
    ],
    temperature=0
)

print("\n================ LLM RESPONSE ================")
print(response.choices[0].message.content)
print("==============================================")
