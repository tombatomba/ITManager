import os
import numpy as np
import faiss
from openai import OpenAI
from config import Config

# Inicijalizacija OpenAI client
client = OpenAI(api_key=Config.OPENAI_API_KEY)

# Folder sa knowledge fajlovima
KNOWLEDGE_DIR = "knowledge/companyinfo"

# Gde ćemo sačuvati FAISS indeks i metadata
os.makedirs("faiss", exist_ok=True)
INDEX_PATH = "faiss/company_info.index"
META_PATH = "faiss/company_info_meta.npy"

texts = []       # Ovo će sadržati male chunk-ove teksta (za embedding)
metadata = []    # Ovo će sadržati samo metapodatke (bez celog teksta!)

# Parametri za chunk-ovanje – prilagodi po potrebi
CHUNK_SIZE = 500      # ~600-800 tokena, dobro za text-embedding-3-large
CHUNK_OVERLAP = 100   # Preklapanje da se ne izgubi kontekst na granici

print("Učitavam i chunk-ujem Markdown fajlove...")

for filename in os.listdir(KNOWLEDGE_DIR):
    if filename.endswith(".md"):
        print(f"Ulaz: {filename}")
        path = os.path.join(KNOWLEDGE_DIR, filename)
        with open(path, "r", encoding="utf-8") as f:
            full_content = f.read().strip()

        if not full_content:
            print("--Ddustajem---------------------------------------------------------------------")
            continue

        print(f"Obradjujem: {filename}")

        # =============================================
        # RUČNO CHUNK-OVANJE (bez LangChain, čisto Python)
        # =============================================
        # Bolji separatori za Markdown: prvo po naslovima, pa paragrafima
        chunks = []
        current_chunk = ""
        lines = full_content.split("\n")

        for line in lines:
            # Privremeno dodaj liniju
            temp_chunk = current_chunk + ("\n" if current_chunk else "") + line

            # Ako je predug, sačuvaj trenutni chunk i počni novi
            if len(temp_chunk) > CHUNK_SIZE and current_chunk:
                chunks.append(current_chunk.strip())
                # Overlap: uzmi poslednjih N karaktera za sledeći chunk
                overlap_start = max(0, len(current_chunk) - CHUNK_OVERLAP)
                current_chunk = current_chunk[overlap_start:]
            else:
                current_chunk = temp_chunk

        # Dodaj poslednji chunk ako postoji
        if current_chunk.strip():
            chunks.append(current_chunk.strip())

        # =============================================
        # Dodaj chunk-ove u liste
        # =============================================
        for chunk_id, chunk_text in enumerate(chunks):
            if chunk_text.strip():  # preskoči prazne
                texts.append(chunk_text)

                metadata.append({
                    "file": filename,
                    "chunk_id": chunk_id,
                    "topic": os.path.basename(KNOWLEDGE_DIR),
                    "source": f"{filename}#chunk{chunk_id}"  # opcionalno: lepši identifikator
                    # NE STAVLJAMO "content": chunk_text OVDE – troši memoriju nepotrebno
                })

if not texts:
    raise ValueError("Nijedan validan chunk nije pronađen u folderu: " + KNOWLEDGE_DIR)

print(f"Pronađeno i chunk-ovano: {len(texts)} chunk-ova iz Markdown fajlova")

# 2️⃣ Kreiraj embeddings za sve chunk-ove
print("Kreiram embeddings...")
response = client.embeddings.create(
    model="text-embedding-3-large",
    input=texts
)

if hasattr(response, "usage"):
    print(f"Ukupno tokena za embedding: {response.usage.total_tokens}")

vectors = [e.embedding for e in response.data]
vectors = np.array(vectors).astype("float32")

# 3️⃣ Kreiraj FAISS indeks
dimension = vectors.shape[1]
index = faiss.IndexFlatL2(dimension)
index.add(vectors)

# 4️⃣ Sačuvaj indeks i metadata
faiss.write_index(index, INDEX_PATH)
# testiram
print(metadata)
np.save(META_PATH, metadata)  # metadata sada ima samo male dict-ove – mnogo lakše

print(f"FAISS indeks uspešno kreiran sa {index.ntotal} chunk-ova")
print(f"Indeks sačuvan na: {INDEX_PATH}")
print(f"Metadata sačuvana na: {META_PATH}")
# === DODAJ OVO NA KRAJ BUILD SKRIPTE ===
TEXTS_PATH = "faiss/company_info_texts.npy"
np.save(TEXTS_PATH, texts)  # texts je lista koju si popunio sa chunk-ovima
print(f"Chunk tekstovi uspešno sačuvani na: {TEXTS_PATH}")
# =========================================