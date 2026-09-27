import os

from dotenv import load_dotenv
from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance,
    VectorParams,
    PointStruct,
    PayloadSchemaType,
)
from sentence_transformers import SentenceTransformer

from server.ingestion import load_documents
from server.chunking import chunk_documents


load_dotenv()

QDRANT_URL = os.getenv("QDRANT_URL")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")

COLLECTION_NAME = "personal_knowledge_base"
MODEL_NAME = "all-MiniLM-L6-v2"
VECTOR_SIZE = 384


if not QDRANT_URL or not QDRANT_API_KEY:
    raise ValueError("QDRANT_URL or QDRANT_API_KEY is missing from .env")


client = QdrantClient(
    url=QDRANT_URL,
    api_key=QDRANT_API_KEY,
)


def create_collection():
    if not client.collection_exists(COLLECTION_NAME):
        client.create_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=VectorParams(
                size=VECTOR_SIZE,
                distance=Distance.COSINE,
            ),
        )
        print(f"Collection '{COLLECTION_NAME}' created.")
    else:
        print(f"Collection '{COLLECTION_NAME}' already exists.")
def create_user_id_index():
    client.create_payload_index(
        collection_name=COLLECTION_NAME,
        field_name="user_id",
        field_schema=PayloadSchemaType.INTEGER,
    )

    print("User ID payload index created.")

def upload_documents(user_id: int = 1):
    print("Loading documents...")

    documents = load_documents()
    chunks = chunk_documents(documents)

    print(f"Documents loaded: {len(documents)}")
    print(f"Chunks created: {len(chunks)}")

    print("Generating embeddings...")

    model = SentenceTransformer(MODEL_NAME)

    texts = [chunk["text"] for chunk in chunks]

    embeddings = model.encode(
        texts,
        show_progress_bar=True,
        normalize_embeddings=True,
    )

    print("Uploading vectors to Qdrant...")

    points = []

    for index, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
        points.append(
            PointStruct(
                id=index,
                vector=embedding.tolist(),
               payload={
    "user_id": user_id,
    "source": chunk["source"],
    "chunk_id": chunk["chunk_id"],
    "text": chunk["text"],
},
            )
        )

    client.upsert(
        collection_name=COLLECTION_NAME,
        points=points,
    )

    print(f"Successfully uploaded {len(points)} chunks to Qdrant.")
def upload_single_document(
    source: str,
    text: str,
    user_id: int,
):
    from server.chunking import chunk_documents
    import hashlib

    document = {
        "source": source,
        "text": text,
    }

    chunks = chunk_documents([document])

    model = SentenceTransformer(MODEL_NAME)

    texts = [chunk["text"] for chunk in chunks]

    embeddings = model.encode(
        texts,
        show_progress_bar=False,
        normalize_embeddings=True,
    )

    points = []

    for chunk, embedding in zip(chunks, embeddings):

        point_key = (
            f"{user_id}:"
            f"{source}:"
            f"{chunk['chunk_id']}"
        )

        point_id = int(
            hashlib.sha256(
                point_key.encode()
            ).hexdigest()[:15],
            16,
        )

        points.append(
            PointStruct(
                id=point_id,
                vector=embedding.tolist(),
                payload={
                    "user_id": user_id,
                    "source": chunk["source"],
                    "chunk_id": chunk["chunk_id"],
                    "text": chunk["text"],
                },
            )
        )

    client.upsert(
        collection_name=COLLECTION_NAME,
        points=points,
    )

    return len(points)
    from server.chunking import chunk_documents

    document = {
        "source": source,
        "text": text,
    }

    chunks = chunk_documents([document])

    model = SentenceTransformer(MODEL_NAME)

    texts = [chunk["text"] for chunk in chunks]

    embeddings = model.encode(
        texts,
        show_progress_bar=False,
        normalize_embeddings=True,
    )

    points = []

    for chunk, embedding in zip(chunks, embeddings):
        point_id = abs(hash(f"{source}:{chunk['chunk_id']}"))

        points.append(
            PointStruct(
                id=point_id,
                vector=embedding.tolist(),
                payload={
                    "source": chunk["source"],
                    "chunk_id": chunk["chunk_id"],
                    "text": chunk["text"],
                },
            )
        )

    client.upsert(
        collection_name=COLLECTION_NAME,
        points=points,
    )

    return len(points)

if __name__ == "__main__":
    create_collection()
    create_user_id_index()
    upload_documents()