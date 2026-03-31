from ai.myopenai import MyOpenAI
from openai import OpenAI
from config import Config



client = OpenAI(api_key=Config.OPENAI_API_KEY)

def embed(texts):
    """
    Kreira embedding za jedan ili više tekstova.
    
    Args:
        texts (str ili list[str]): tekst ili lista tekstova
    
    Returns:
        embedding (list[float]) ako je jedan tekst,
        ili lista embeddinga ako je više tekstova
    """
    # normalizuj input u listu
    if isinstance(texts, str):
        texts = [texts]
    elif not isinstance(texts, list):
        raise ValueError("texts must be a string or a list of strings")
    
    # filtriraj prazne tekstove
    texts = [t for t in texts if t.strip()]
    if not texts:
        raise ValueError("No valid text provided for embedding")
    
    response = client.embeddings.create(
        model="text-embedding-3-large",
        input=texts
    )
    
    embeddings = [e.embedding for e in response.data]
    
    # ako je samo jedan tekst, vrati samo embedding
    if len(embeddings) == 1:
        return embeddings[0]
    return embeddings