from pathlib import Path
from pypdf import PdfReader


DOCUMENTS_DIR = Path(__file__).resolve().parent.parent / "documents"


def extract_text_from_pdf(pdf_path: Path) -> str:
    """Extract all readable text from a PDF."""
    reader = PdfReader(pdf_path)

    pages_text = []

    for page in reader.pages:
        text = page.extract_text() or ""
        pages_text.append(text)

    return "\n".join(pages_text)


def load_documents():
    """Load all PDF documents from the documents folder."""
    documents = []

    for pdf_path in sorted(DOCUMENTS_DIR.glob("*.pdf")):
        text = extract_text_from_pdf(pdf_path)

        documents.append({
            "source": pdf_path.name,
            "text": text,
        })

    return documents


if __name__ == "__main__":
    documents = load_documents()

    print(f"Found {len(documents)} PDF documents.\n")

    for document in documents:
        print(f"Source: {document['source']}")
        print(f"Characters: {len(document['text'])}")
        print(f"Preview: {document['text'][:300]}")
        print("-" * 60)