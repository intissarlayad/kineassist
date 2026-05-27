"""
Script d'indexation RAG - A lancer UNE FOIS avant de demarrer l'app.
Lit les vrais documents medicaux et construit l'index FAISS.
"""

import os
import sys
from pathlib import Path

print("=== Construction de l'index RAG ===")
print("Verification des dependances...")

# Verif dependances
missing = []
try:
    from sentence_transformers import SentenceTransformer
except ImportError:
    missing.append("sentence-transformers")

try:
    import faiss
except ImportError:
    missing.append("faiss-cpu")

try:
    import numpy as np
except ImportError:
    missing.append("numpy")

if missing:
    print(f"ERREUR : Packages manquants : {', '.join(missing)}")
    print(f"Lancez : pip install {' '.join(missing)}")
    sys.exit(1)

import numpy as np
import json
import pickle

print("OK - Dependances disponibles")

# ── Chargement des documents ──────────────────────────────────────────────────
PROTOCOLS_DIR = Path("data/protocols")
docs = []

print(f"\nChargement des documents depuis {PROTOCOLS_DIR}/")
for txt_file in sorted(PROTOCOLS_DIR.glob("*.txt")):
    content = txt_file.read_text(encoding="utf-8")
    docs.append({
        "source":  txt_file.name,
        "content": content,
    })
    print(f"  Charge : {txt_file.name} ({len(content)} chars)")

if not docs:
    print("ERREUR : Aucun document trouve dans data/protocols/")
    sys.exit(1)

# ── Chunking ──────────────────────────────────────────────────────────────────
print(f"\nDecoupage en chunks...")
CHUNK_SIZE   = 400
CHUNK_OVERLAP = 60

chunks = []
for doc in docs:
    text   = doc["content"]
    source = doc["source"]
    words  = text.split()
    step   = CHUNK_SIZE - CHUNK_OVERLAP

    for i in range(0, len(words), step):
        chunk_words = words[i:i + CHUNK_SIZE]
        chunk_text  = " ".join(chunk_words)
        if len(chunk_text.strip()) > 50:
            chunks.append({
                "text":   chunk_text,
                "source": source,
                "idx":    len(chunks),
            })

print(f"  {len(chunks)} chunks crees depuis {len(docs)} documents")

# ── Embeddings ────────────────────────────────────────────────────────────────
print("\nCalcul des embeddings (modele local, pas d'API necessaire)...")
model = SentenceTransformer("all-MiniLM-L6-v2")

texts      = [c["text"] for c in chunks]
embeddings = model.encode(texts, show_progress_bar=True, batch_size=32)
embeddings = embeddings.astype(np.float32)

print(f"  Shape embeddings : {embeddings.shape}")

# ── Index FAISS ───────────────────────────────────────────────────────────────
print("\nConstruction de l'index FAISS...")
dim   = embeddings.shape[1]
index = faiss.IndexFlatIP(dim)

# Normalisation pour cosine similarity
faiss.normalize_L2(embeddings)
index.add(embeddings)

print(f"  Index construit : {index.ntotal} vecteurs de dimension {dim}")

# ── Sauvegarde ────────────────────────────────────────────────────────────────
OUTPUT_DIR = Path("data/rag_index")
OUTPUT_DIR.mkdir(exist_ok=True)

faiss.write_index(index, str(OUTPUT_DIR / "medical.index"))

with open(OUTPUT_DIR / "chunks.pkl", "wb") as f:
    pickle.dump(chunks, f)

with open(OUTPUT_DIR / "meta.json", "w", encoding="utf-8") as f:
    json.dump({
        "n_docs":   len(docs),
        "n_chunks": len(chunks),
        "dim":      dim,
        "model":    "all-MiniLM-L6-v2",
        "sources":  [d["source"] for d in docs],
    }, f, ensure_ascii=False, indent=2)

print(f"\n=== Index RAG sauvegarde dans {OUTPUT_DIR}/ ===")
print(f"  medical.index : {(OUTPUT_DIR/'medical.index').stat().st_size // 1024} KB")
print(f"  chunks.pkl    : {len(chunks)} chunks")
print(f"\nL'app peut maintenant utiliser le RAG reel.")
print("Lancez : streamlit run app.py")