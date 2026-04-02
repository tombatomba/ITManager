import faiss
import numpy as np
from AIConfig import AIConfig
from openai import OpenAI
from config import Config
from models import CompanyKnowledge, KnowledgeEmbedding, TeamKnowledge, db # Uvezi tvoj novi model

class ContextService:
    def __init__(self, team_id=None, company_id=None):
        self.client = OpenAI(api_key=AIConfig.get('OPENAI_API_KEY'))
        self.texts = []
        self.metadata = []
        
        # Inicijalizacija FAISS indeksa u RAM-u
        # Dimenzija 3072 je za 'text-embedding-3-large'
        self.dimension = 3072
        self.index = faiss.IndexFlatL2(self.dimension)

        # Učitavanje podataka iz baze umesto fajlova
        self._load_from_db(team_id, company_id)
        
        # Kompatibilnost
        self.store = self

    def _load_from_db(self, team_id, company_id):
        from sqlalchemy import or_
        
        # 1. Definišemo upit sa OR logikom (Team ILI Company)
        query = KnowledgeEmbedding.query\
            .outerjoin(TeamKnowledge, KnowledgeEmbedding.KnowledgeID == TeamKnowledge.ID)\
            .outerjoin(CompanyKnowledge, KnowledgeEmbedding.KnowledgeID == CompanyKnowledge.ID)\
            .filter(
                or_(
                    (KnowledgeEmbedding.TeamID == team_id) & (KnowledgeEmbedding.Scope == 'team'),
                    (KnowledgeEmbedding.CompanyID == company_id) & (KnowledgeEmbedding.Scope == 'company')
                )
            )
        
        results = query.all()
        
        if not results:
            print("ContextService: Nema podataka u bazi za ovaj kontekst.")
            return

        # Ovde koristimo dosledno ime: all_vectors
        all_vectors = [] 
        for res in results:
            # 2. Logika za izvlačenje fileName-a
        # Proveravamo koji join je vratio rezultat na osnovu Scope-a
            current_file_name = "unknown"        
            if res.Scope == 'team':    
                t_knowledge = TeamKnowledge.query.get(res.KnowledgeID)
                current_file_name = t_knowledge.FileName if t_knowledge else "unknown"
            
            elif res.Scope == 'company':
                c_knowledge = CompanyKnowledge.query.get(res.KnowledgeID)
                current_file_name = c_knowledge.FileName if c_knowledge else "unknown"
            self.texts.append(res.ChunkText)
            self.metadata.append({
                "knowledge_id": str(res.KnowledgeID),
                "scope": res.Scope,
                "file_name": current_file_name
            })
                
            # Konverzija iz binarnog SQL formata u numpy array
            vector = np.frombuffer(res.Embedding, dtype="float32")
            all_vectors.append(vector)

        # 2. DODAVANJE U FAISS
        if all_vectors:
            # Ovde je bila greška - sada je ispravljeno na all_vectors
            v_matrix = np.array(all_vectors).astype("float32") 
            
            # Provera dimenzije pre dodavanja (mora biti 3072)
            if v_matrix.shape[1] == self.dimension:
                self.index.add(v_matrix)
                print(f"ContextService: Uspešno učitano {self.index.ntotal} chunk-ova.")
            else:
                print(f"Greška: Dimenzija vektora u bazi ({v_matrix.shape[1]}) se ne poklapa sa FAISS ({self.dimension})")

    def embed(self, text: str):
        response = self.client.embeddings.create(
            model="text-embedding-3-large",
            input=text
        )
        return np.array(response.data[0].embedding).astype("float32")

    def search(self, query_vector, k=4):
        # Ako je indeks prazan, vrati ništa
        if self.index.ntotal == 0:
            return []
            
        D, I = self.index.search(np.array([query_vector]).astype("float32"), k)
        results = []
        for idx in I[0]:
            if idx != -1 and idx < len(self.texts):
                results.append({
                    "content": self.texts[idx],
                    "metadata": self.metadata[idx]
                })
        return results

    def get_context(self, prompt: str, k: int = 4) -> str:
        query_vector = self.embed(prompt)
        matches = self.search(query_vector, k)
        
        context_parts = [m.get("content").strip() for m in matches if m.get("content")]
        return "\n\n---\n\n".join(context_parts)

    #Metoda koja ima i izvor podataka i u njoj  isecam system_structured_data
    def get_context2(self, prompt: str, k: int = 4) -> str:
        query_vector = self.embed(prompt)
        matches = self.search(query_vector, k)

        context_parts = []
        for m in matches:            
            meta = m['metadata']
            if meta['file_name']!='SYSTEM_STRUCTURED_DATA.md':
                header = f"[Izvor: {meta['scope'].capitalize()} Doc ID: {meta['knowledge_id'][:8]}]"
                part = f"{header}\n{m['content'].strip()}"
                context_parts.append(part)

        return "\n\n---\n\n".join(context_parts)