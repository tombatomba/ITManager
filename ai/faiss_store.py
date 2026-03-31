import os
import faiss
import numpy as np

class FaissStore:
    def __init__(self, index_path, metadata_path):
        index_path = os.path.abspath(index_path)
        metadata_path = os.path.abspath(metadata_path)

        if not os.path.exists(index_path):
            raise FileNotFoundError(f"FAISS index file not found: {index_path}")
        if not os.path.exists(metadata_path):
            raise FileNotFoundError(f"FAISS metadata file not found: {metadata_path}")

        self.index = faiss.read_index(index_path)
        self.metadata = np.load(metadata_path, allow_pickle=True)

    def search(self, query_vector, k=5):
        D, I = self.index.search(
            np.array([query_vector]).astype("float32"),
            k
        )

        results = []
        for idx in I[0]:
            if idx < len(self.metadata):
                results.append(self.metadata[idx])

        return results