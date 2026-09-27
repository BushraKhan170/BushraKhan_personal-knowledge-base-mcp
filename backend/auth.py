import sqlite3
import hashlib
import secrets
import jwt
import os
import sqlite3
import hashlib
import secrets
import jwt

from datetime import datetime, timedelta, timezone
from pathlib import Path

from dotenv import load_dotenv


load_dotenv()


DB_PATH = Path(__file__).resolve().parent / "users.db"

SECRET_KEY = os.getenv("JWT_SECRET_KEY")

if not SECRET_KEY:
    raise ValueError("JWT_SECRET_KEY is missing from .env")

ALGORITHM = "HS256"
from datetime import datetime, timedelta, timezone
from pathlib import Path


DB_PATH = Path(__file__).resolve().parent / "users.db"


ALGORITHM = "HS256"


def get_connection():
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def init_db():
    connection = get_connection()

    connection.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
    """)

    connection.execute("""
        CREATE TABLE IF NOT EXISTS documents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            filename TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
    """)

    connection.execute("""
        CREATE TABLE IF NOT EXISTS search_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            query TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
    """)

    connection.commit()
    connection.close()


def hash_password(password: str, salt: str | None = None):
    if salt is None:
        salt = secrets.token_hex(16)

    password_hash = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode(),
        salt.encode(),
        100000,
    ).hex()

    return f"{salt}${password_hash}"


def verify_password(password: str, stored_password: str):
    salt, stored_hash = stored_password.split("$")

    password_hash = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode(),
        salt.encode(),
        100000,
    ).hex()

    return secrets.compare_digest(
        password_hash,
        stored_hash,
    )


def create_user(name: str, email: str, password: str):
    connection = get_connection()

    try:
        password_hash = hash_password(password)

        cursor = connection.execute(
            """
            INSERT INTO users
            (name, email, password_hash, created_at)
            VALUES (?, ?, ?, ?)
            """,
            (
                name,
                email.lower(),
                password_hash,
                datetime.now(timezone.utc).isoformat(),
            ),
        )

        connection.commit()

        return {
            "id": cursor.lastrowid,
            "name": name,
            "email": email.lower(),
        }

    except sqlite3.IntegrityError:
        return None

    finally:
        connection.close()


def authenticate_user(email: str, password: str):
    connection = get_connection()

    user = connection.execute(
        "SELECT * FROM users WHERE email = ?",
        (email.lower(),),
    ).fetchone()

    connection.close()

    if not user:
        return None

    if not verify_password(
        password,
        user["password_hash"],
    ):
        return None

    return {
        "id": user["id"],
        "name": user["name"],
        "email": user["email"],
    }


def create_token(user: dict):
    payload = {
        "user_id": user["id"],
        "email": user["email"],
        "exp": datetime.now(timezone.utc)
        + timedelta(hours=24),
    }

    return jwt.encode(
        payload,
        SECRET_KEY,
        algorithm=ALGORITHM,
    )


def decode_token(token: str):
    try:
        return jwt.decode(
            token,
            SECRET_KEY,
            algorithms=[ALGORITHM],
        )

    except jwt.PyJWTError:
        return None


def add_document(user_id: int, filename: str):
    connection = get_connection()

    connection.execute(
        """
        INSERT INTO documents
        (user_id, filename, created_at)
        VALUES (?, ?, ?)
        """,
        (
            user_id,
            filename,
            datetime.now(timezone.utc).isoformat(),
        ),
    )

    connection.commit()
    connection.close()


def get_user_documents(user_id: int):
    connection = get_connection()

    documents = connection.execute(
        """
        SELECT filename, created_at
        FROM documents
        WHERE user_id = ?
        ORDER BY created_at DESC
        """,
        (user_id,),
    ).fetchall()

    connection.close()

    return [
        {
            "filename": document["filename"],
            "created_at": document["created_at"],
        }
        for document in documents
    ]


def add_search_history(user_id: int, query: str):
    connection = get_connection()

    connection.execute(
        """
        INSERT INTO search_history
        (user_id, query, created_at)
        VALUES (?, ?, ?)
        """,
        (
            user_id,
            query,
            datetime.now(timezone.utc).isoformat(),
        ),
    )

    connection.commit()
    connection.close()


def get_search_history(user_id: int):
    connection = get_connection()

    history = connection.execute(
        """
        SELECT query, created_at
        FROM search_history
        WHERE user_id = ?
        ORDER BY created_at DESC
        LIMIT 20
        """,
        (user_id,),
    ).fetchall()

    connection.close()

    return [
        {
            "query": item["query"],
            "created_at": item["created_at"],
        }
        for item in history
    ]