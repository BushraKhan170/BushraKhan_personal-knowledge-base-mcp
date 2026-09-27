from typing import List, Dict


# Approximate chunk size in characters
CHUNK_SIZE = 1200

# Number of characters that overlap between consecutive chunks
CHUNK_OVERLAP = 200


def chunk_text(text: str) -> List[str]:
    """
    Split text into overlapping chunks.

    The overlap helps preserve context when an important
    sentence falls near a chunk boundary.
    """

    text = text.strip()

    if not text:
        return []

    chunks = []
    start = 0

    while start < len(text):
        end = start + CHUNK_SIZE
        chunk = text[start:end].strip()

        if chunk:
            chunks.append(chunk)

        if end >= len(text):
            break

        start = end - CHUNK_OVERLAP

    return chunks


def chunk_documents(documents: List[Dict]) -> List[Dict]:
    """
    Chunk all loaded documents while preserving their source names.
    """

    all_chunks = []

    for document in documents:
        chunks = chunk_text(document["text"])

        for index, chunk in enumerate(chunks):
            all_chunks.append({
                "source": document["source"],
                "chunk_id": index,
                "text": chunk,
            })

    return all_chunks


if __name__ == "__main__":
    # Import our PDF loader
    from ingestion import load_documents

    documents = load_documents()
    chunks = chunk_documents(documents)

    print(f"Documents loaded: {len(documents)}")
    print(f"Total chunks created: {len(chunks)}")
    print()

    for chunk in chunks[:5]:
        print(f"Source: {chunk['source']}")
        print(f"Chunk ID: {chunk['chunk_id']}")
        print(f"Characters: {len(chunk['text'])}")
        print(f"Preview: {chunk['text'][:300]}")
        print("-" * 60)