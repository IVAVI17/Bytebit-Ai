import numpy as np
import faiss
from sentence_transformers import SentenceTransformer
from db import run_read_query

model = SentenceTransformer("all-MiniLM-L6-v2")

dimension = 384
index = faiss.IndexFlatL2(dimension)

metadata = []


def build_index():
    """Build FAISS index from analytics sheet"""
    
    # Fetch all records from Google Sheets
    rows = run_read_query("SELECT * FROM analytics")
    
    for row in rows:
        text = f"{row.get('symptoms', '')} {row.get('patient_notes', '')} {row.get('doctor_notes', '')}"
        
        if text.strip():  # Only add if there's content
            embedding = model.encode(text)
            index.add(np.array([embedding]).astype("float32"))
            metadata.append(row)

def semantic_search(query, k=5):
    """Search using semantic similarity"""
    
    embedding = model.encode(query)
    D, I = index.search(np.array([embedding]).astype("float32"), k)
    
    results = []
    for idx in I[0]:
        if idx < len(metadata):
            results.append(metadata[idx])
    
    return results