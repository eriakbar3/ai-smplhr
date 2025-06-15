import faiss
import os
import pickle
from sentence_transformers import SentenceTransformer

# Path simpan index dan metadata
VECTOR_PATH = os.getenv('VECTOR_PATH', './')
INDEX_PATH = os.path.join(VECTOR_PATH, "faiss_index.index")
META_PATH = os.path.join(VECTOR_PATH, "faiss_meta.pkl")

# Load model embedding
model = SentenceTransformer('all-MiniLM-L6-v2')
dimension = 384  # sesuai dengan model

# Inisialisasi index dan metadata
if os.path.exists(INDEX_PATH):
    index = faiss.read_index(INDEX_PATH)
    with open(META_PATH, 'rb') as f:
        id_list, content_dict = pickle.load(f)
else:
    index = faiss.IndexFlatL2(dimension)
    id_list = []           # urutan ID berdasarkan posisi di FAISS
    content_dict = {}      # mapping dari ID ke isi dokumen

def store_to_vector_db(id: str, text: str) -> str:
    embedding = model.encode([text])
    index.add(embedding)
    id_list.append(id)
    content_dict[id] = text

    # Persist
    faiss.write_index(index, INDEX_PATH)
    with open(META_PATH, 'wb') as f:
        pickle.dump((id_list, content_dict), f)

    return id

def search_vector_db(query: str, top_k: int = 5):
    if index.ntotal == 0:
        return []

    query_embedding = model.encode([query])
    D, I = index.search(query_embedding, top_k)

    results = []
    for idx in I[0]:
        if idx < len(id_list):
            vector_id = id_list[idx]
            results.append({
                "id": vector_id,
                "content": content_dict.get(vector_id)
            })
    return results
