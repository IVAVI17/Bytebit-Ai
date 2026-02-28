import numpy as np
import faiss
from sentence_transformers import SentenceTransformer
from db import run_read_query

model = SentenceTransformer("all-MiniLM-L6-v2")

dimension = 384
index = faiss.IndexFlatL2(dimension)

metadata = []


def build_index():

    rows = run_read_query("SELECT * FROM master")

    for row in rows:

        text = f"{row['symptoms']} {row['patient_notes']} {row['doctor_notes']}"

        embedding = model.encode(text)

        index.add(np.array([embedding]).astype("float32"))

        metadata.append(row)


def semantic_search(query, k=5):

    embedding = model.encode(query)

    D, I = index.search(np.array([embedding]).astype("float32"), k)

    results = []

    for idx in I[0]:
        if idx < len(metadata):
            results.append(metadata[idx])

    return results