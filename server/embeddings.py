from sentence_transformers import SentenceTransformer

from ingestion import load_documents
from chunking import chunk_documents


MODEL_NAME = "all-MiniLM-L6-v2"


def generate_embeddings(chunks):
    """Generate an embedding vector for each chunk."""
    model = SentenceTransformer(MODEL_NAME)

    texts = [chunk["text"] for chunk in chunks]

    embeddings = model.encode(
        texts,
        show_progress_bar=True,
        normalize_embeddings=True,
    )

    return embeddings


if __name__ == "__main__":
    documents = load_documents()
    chunks = chunk_documents(documents)

    print(f"Generating embeddings for {len(chunks)} chunks...")

    embeddings = generate_embeddings(chunks)

    print(f"\nEmbeddings generated successfully!")
    print(f"Number of embeddings: {len(embeddings)}")
    print(f"Embedding dimensions: {embeddings.shape[1]}")
    print(f"First embedding preview: {embeddings[0][:10]}")