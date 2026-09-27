from fastmcp import FastMCP

from search import search_knowledge_base
from ingestion import load_documents


mcp = FastMCP("Personal Knowledge Base")


@mcp.tool
def search_knowledge(query: str, limit: int = 5) -> list[dict]:
    """
    Search the personal knowledge base using semantic search.
    Returns ranked chunks with source and similarity score.
    """
    return search_knowledge_base(query, limit)


@mcp.tool
def list_documents() -> list[str]:
    """
    List all documents currently available in the knowledge base.
    """
    documents = load_documents()
    return [document["source"] for document in documents]


@mcp.tool
def get_document_context(source: str) -> dict:
    """
    Retrieve the full text of a document from the knowledge base.
    """
    documents = load_documents()

    for document in documents:
        if document["source"] == source:
            return {
                "source": document["source"],
                "text": document["text"],
            }

    return {
        "error": f"Document '{source}' was not found."
    }


if __name__ == "__main__":
    mcp.run()