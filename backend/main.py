import shutil

from pathlib import Path

from fastapi import (
    FastAPI,
    UploadFile,
    File,
    HTTPException,
    Header,
)

from fastapi.middleware.cors import CORSMiddleware

from pydantic import BaseModel

from backend.auth import (
    init_db,
    create_user,
    authenticate_user,
    create_token,
    decode_token,
    add_document,
    get_user_documents,
    add_search_history,
    get_search_history,
)

from server.ingestion import extract_text_from_pdf
from server.qdrant_store import upload_single_document
from server.search import search_knowledge_base


app = FastAPI(
    title="Personal Knowledge Base API",
    description="API for the Personal Knowledge Base MCP project",
    version="1.0.0",
)


init_db()


app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


class SignupRequest(BaseModel):
    name: str
    email: str
    password: str


class LoginRequest(BaseModel):
    email: str
    password: str


def get_current_user(
    authorization: str | None,
):
    if not authorization:
        raise HTTPException(
            status_code=401,
            detail="Authentication required.",
        )

    if not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=401,
            detail="Invalid authentication format.",
        )

    token = authorization.replace(
        "Bearer ",
        "",
        1,
    )

    payload = decode_token(token)

    if not payload:
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired token.",
        )

    return payload


@app.post("/auth/signup")
def signup(data: SignupRequest):

    if len(data.password) < 6:
        raise HTTPException(
            status_code=400,
            detail="Password must be at least 6 characters.",
        )

    user = create_user(
        data.name,
        data.email,
        data.password,
    )

    if user is None:
        raise HTTPException(
            status_code=400,
            detail="An account with this email already exists.",
        )

    token = create_token(user)

    return {
        "message": "Account created successfully.",
        "token": token,
        "user": user,
    }


@app.post("/auth/login")
def login(data: LoginRequest):

    user = authenticate_user(
        data.email,
        data.password,
    )

    if user is None:
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password.",
        )

    token = create_token(user)

    return {
        "message": "Login successful.",
        "token": token,
        "user": user,
    }


@app.get("/")
def root():
    return {
        "message": "Personal Knowledge Base API is running"
    }


@app.get("/health")
def health():
    return {
        "status": "healthy"
    }


@app.get("/search")
def search(
    query: str,
    limit: int = 5,
    authorization: str | None = Header(
        default=None
    ),
):

    user = get_current_user(authorization)

    user_id = int(user["user_id"])

    results = search_knowledge_base(
        query,
        limit,
        user_id,
    )

    add_search_history(
        user_id,
        query,
    )

    return {
        "query": query,
        "results": results,
    }


@app.get("/documents")
def get_documents(
    authorization: str | None = Header(
        default=None
    ),
):

    user = get_current_user(authorization)

    user_id = int(user["user_id"])

    documents = get_user_documents(user_id)

    return {
        "documents": documents
    }


UPLOAD_DIR = Path("backend/uploads")
UPLOAD_DIR.mkdir(
    parents=True,
    exist_ok=True,
)


@app.post("/upload")
async def upload_document(
    file: UploadFile = File(...),
    authorization: str | None = Header(
        default=None
    ),
):

    user = get_current_user(authorization)

    user_id = int(user["user_id"])

    if not file.filename:
        raise HTTPException(
            status_code=400,
            detail="No filename provided.",
        )

    extension = Path(
        file.filename
    ).suffix.lower()

    if extension != ".pdf":
        raise HTTPException(
            status_code=400,
            detail="Only PDF files are supported right now.",
        )

    safe_filename = Path(
        file.filename
    ).name

    user_upload_dir = (
        UPLOAD_DIR / str(user_id)
    )

    user_upload_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    file_path = (
        user_upload_dir / safe_filename
    )

    with open(
        file_path,
        "wb",
    ) as buffer:

        shutil.copyfileobj(
            file.file,
            buffer,
        )

    try:

        text = extract_text_from_pdf(
            file_path
        )

        if not text.strip():
            raise HTTPException(
                status_code=400,
                detail=(
                    "Could not extract readable "
                    "text from the PDF."
                ),
            )

        chunk_count = upload_single_document(
            source=safe_filename,
            text=text,
            user_id=user_id,
        )

        add_document(
            user_id,
            safe_filename,
        )

        return {
            "message": (
                "Document uploaded and "
                "indexed successfully."
            ),
            "filename": safe_filename,
            "chunks_indexed": chunk_count,
        }

    except HTTPException:
        raise

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=(
                "Failed to process document: "
                f"{str(e)}"
            ),
        )


@app.get("/history")
def history(
    authorization: str | None = Header(
        default=None
    ),
):

    user = get_current_user(authorization)

    user_id = int(user["user_id"])

    return {
        "history": get_search_history(
            user_id
        )
    }