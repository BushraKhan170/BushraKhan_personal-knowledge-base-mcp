import os

from dotenv import load_dotenv

from qdrant_client import QdrantClient
from qdrant_client.models import (
    Filter,
    FieldCondition,
    MatchValue,
)

from sentence_transformers import SentenceTransformer


load_dotenv()


QDRANT_URL = os.getenv("QDRANT_URL")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")

COLLECTION_NAME = "personal_knowledge_base"
MODEL_NAME = "all-MiniLM-L6-v2"

SIMILARITY_THRESHOLD = 0.45


client = QdrantClient(
    url=QDRANT_URL,
    api_key=QDRANT_API_KEY,
)

model = SentenceTransformer(MODEL_NAME)


def search_knowledge_base(
    query: str,
    limit: int = 5,
    user_id: int | None = None,
):

    query_embedding = model.encode(
        query,
        normalize_embeddings=True,
    ).tolist()

    query_filter = None

    if user_id is not None:
        query_filter = Filter(
            must=[
                FieldCondition(
                    key="user_id",
                    match=MatchValue(
                        value=user_id
                    ),
                )
            ]
        )

    results = client.query_points(
        collection_name=COLLECTION_NAME,
        query=query_embedding,
        query_filter=query_filter,
        limit=limit,
        with_payload=True,
    )

    matches = []

    for result in results.points:

        if result.score >= SIMILARITY_THRESHOLD:

            matches.append({
                "score": result.score,
                "source": result.payload["source"],
                "chunk_id": result.payload["chunk_id"],
                "text": result.payload["text"],
            })

    if not matches:

        return [{
            "score": 0.0,
            "source": None,
            "chunk_id": None,
            "text": "No confident match found for this query.",
        }]

    return matches