"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";

const API_URL = "http://127.0.0.1:8000";

type User = {
  id: number;
  name: string;
  email: string;
};

type SearchResult = {
  score: number;
  source: string | null;
  chunk_id: number | null;
  text: string;
};

type Document = {
  filename: string;
  created_at: string;
};

type HistoryItem = {
  query: string;
  created_at: string;
};

export default function Home() {
  const router = useRouter();

  const [user, setUser] = useState<User | null>(null);

  const [query, setQuery] = useState("");
  const [results, setResults] = useState<SearchResult[]>([]);

  const [documents, setDocuments] = useState<Document[]>([]);
  const [history, setHistory] = useState<HistoryItem[]>([]);

  const [loading, setLoading] = useState(false);
  const [uploading, setUploading] = useState(false);

  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  // --------------------------------------------------
  // Authentication
  // --------------------------------------------------

  useEffect(() => {
    const token = localStorage.getItem("token");
    const savedUser = localStorage.getItem("user");

    if (!token || !savedUser) {
      router.push("/login");
      return;
    }

    try {
      setUser(JSON.parse(savedUser));
    } catch {
      localStorage.removeItem("token");
      localStorage.removeItem("user");
      router.push("/login");
    }
  }, [router]);

  // --------------------------------------------------
  // Load documents
  // --------------------------------------------------

  const loadDocuments = async () => {
    try {
      const token = localStorage.getItem("token");

      const response = await fetch(
        `${API_URL}/documents`,
        {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        }
      );

      if (response.status === 401) {
        logout();
        return;
      }

      if (!response.ok) {
        throw new Error("Failed to load documents");
      }

      const data = await response.json();

      setDocuments(data.documents || []);
    } catch (error) {
      console.error("Document loading error:", error);
    }
  };

  // --------------------------------------------------
  // Load search history
  // --------------------------------------------------

  const loadHistory = async () => {
    try {
      const token = localStorage.getItem("token");

      const response = await fetch(
        `${API_URL}/history`,
        {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        }
      );

      if (response.status === 401) {
        logout();
        return;
      }

      if (!response.ok) {
        throw new Error("Failed to load search history");
      }

      const data = await response.json();

      setHistory(data.history || []);
    } catch (error) {
      console.error("History loading error:", error);
    }
  };

  // --------------------------------------------------
  // Load dashboard data after login
  // --------------------------------------------------

  useEffect(() => {
    const token = localStorage.getItem("token");

    if (!token) {
      return;
    }

    loadDocuments();
    loadHistory();
  }, []);

  // --------------------------------------------------
  // Search knowledge base
  // --------------------------------------------------

  const searchKnowledge = async () => {
    if (!query.trim()) {
      setError("Please enter a search question.");
      return;
    }

    setLoading(true);
    setError("");
    setMessage("");

    try {
      const token = localStorage.getItem("token");

      const response = await fetch(
        `${API_URL}/search?query=${encodeURIComponent(
          query
        )}&limit=5`,
        {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        }
      );

      if (response.status === 401) {
        logout();
        return;
      }

      if (!response.ok) {
        throw new Error("Search failed");
      }

      const data = await response.json();

      setResults(data.results || []);

      // Refresh search history after every search
      await loadHistory();
    } catch (error) {
      console.error("Search error:", error);
      setError("Unable to perform search.");
    } finally {
      setLoading(false);
    }
  };

  // --------------------------------------------------
  // Upload PDF
  // --------------------------------------------------

  const uploadDocument = async (
    event: React.ChangeEvent<HTMLInputElement>
  ) => {
    const file = event.target.files?.[0];

    if (!file) {
      return;
    }

    if (!file.name.toLowerCase().endsWith(".pdf")) {
      setError("Only PDF files are supported.");
      return;
    }

    setUploading(true);
    setError("");
    setMessage("");

    try {
      const token = localStorage.getItem("token");

      const formData = new FormData();

      formData.append("file", file);

      const response = await fetch(
        `${API_URL}/upload`,
        {
          method: "POST",
          headers: {
            Authorization: `Bearer ${token}`,
          },
          body: formData,
        }
      );

      if (response.status === 401) {
        logout();
        return;
      }

      const data = await response.json();

      if (!response.ok) {
        throw new Error(
          data.detail || "Upload failed"
        );
      }

      setMessage(
        `${data.filename} uploaded and indexed successfully.`
      );

      // Refresh document list
      await loadDocuments();

    } catch (error) {
      console.error("Upload error:", error);

      setError(
        error instanceof Error
          ? error.message
          : "Upload failed."
      );
    } finally {
      setUploading(false);

      // Allow selecting the same file again
      event.target.value = "";
    }
  };

  // --------------------------------------------------
  // Logout
  // --------------------------------------------------

  const logout = () => {
    localStorage.removeItem("token");
    localStorage.removeItem("user");

    router.push("/login");
  };

  // --------------------------------------------------
  // Don't render dashboard before authentication check
  // --------------------------------------------------

  if (!user) {
    return (
      <main className="flex min-h-screen items-center justify-center bg-slate-950 text-white">
        <p className="text-slate-400">
          Checking authentication...
        </p>
      </main>
    );
  }

  // --------------------------------------------------
  // Dashboard
  // --------------------------------------------------

  return (
    <main className="min-h-screen bg-slate-950 text-white">
      {/* Header */}
      <header className="border-b border-slate-800 bg-slate-950">
        <div className="mx-auto flex max-w-7xl items-center justify-between px-6 py-5">
          <div>
            <h1 className="text-2xl font-bold">
              Personal Knowledge Base
            </h1>

            <p className="mt-1 text-sm text-slate-400">
              Semantic search powered by Qdrant + MCP
            </p>
          </div>

          <div className="flex items-center gap-4">
            {/* User information */}
            <div className="hidden text-right sm:block">
              <p className="text-sm font-medium">
                {user.name}
              </p>

              <p className="text-xs text-slate-500">
                {user.email}
              </p>
            </div>

            {/* System status */}
            <div className="rounded-full bg-emerald-500/10 px-4 py-2 text-sm text-emerald-400">
              ● System Online
            </div>

            {/* Logout */}
            <button
              onClick={logout}
              className="rounded-lg border border-slate-700 px-4 py-2 text-sm transition hover:bg-slate-800"
            >
              Logout
            </button>
          </div>
        </div>
      </header>

      {/* Main content */}
      <div className="mx-auto max-w-7xl px-6 py-8">

        {/* Welcome */}
        <section className="mb-8">
          <h2 className="text-3xl font-bold">
            Welcome, {user.name}
          </h2>

          <p className="mt-2 text-slate-400">
            Search your personal knowledge base or upload
            new documents.
          </p>
        </section>

        {/* Stats */}
        <section className="grid gap-4 md:grid-cols-3">

          {/* Documents */}
          <div className="rounded-2xl border border-slate-800 bg-slate-900 p-6">
            <p className="text-sm text-slate-400">
              Indexed Documents
            </p>

            <p className="mt-2 text-3xl font-bold">
              {documents.length}
            </p>

            <p className="mt-2 text-xs text-slate-500">
              Your uploaded knowledge sources
            </p>
          </div>

          {/* Search */}
          <div className="rounded-2xl border border-slate-800 bg-slate-900 p-6">
            <p className="text-sm text-slate-400">
              Semantic Search
            </p>

            <p className="mt-2 text-3xl font-bold">
              AI
            </p>

            <p className="mt-2 text-xs text-slate-500">
              Meaning-based document retrieval
            </p>
          </div>

          {/* Qdrant */}
          <div className="rounded-2xl border border-slate-800 bg-slate-900 p-6">
            <p className="text-sm text-slate-400">
              Vector Database
            </p>

            <p className="mt-2 text-3xl font-bold">
              Qdrant
            </p>

            <p className="mt-2 text-xs text-slate-500">
              Cloud vector storage
            </p>
          </div>
        </section>

        {/* Messages */}
        {message && (
          <div className="mt-6 rounded-xl border border-emerald-800 bg-emerald-950/30 p-4 text-sm text-emerald-400">
            {message}
          </div>
        )}

        {error && (
          <div className="mt-6 rounded-xl border border-red-800 bg-red-950/30 p-4 text-sm text-red-400">
            {error}
          </div>
        )}

        {/* Search */}
        <section className="mt-8 rounded-2xl border border-slate-800 bg-slate-900 p-6">
          <h2 className="text-xl font-semibold">
            Search Knowledge Base
          </h2>

          <p className="mt-1 text-sm text-slate-400">
            Ask a question about your indexed documents.
          </p>

          <div className="mt-5 flex flex-col gap-3 sm:flex-row">
            <input
              type="text"
              value={query}
              onChange={(e) => {
                setQuery(e.target.value);
                setError("");
              }}
              onKeyDown={(e) => {
                if (e.key === "Enter") {
                  searchKnowledge();
                }
              }}
              placeholder="Example: How does merge sort work?"
              className="flex-1 rounded-xl border border-slate-700 bg-slate-800 px-4 py-3 text-white outline-none placeholder:text-slate-500 focus:border-blue-500"
            />

            <button
              onClick={searchKnowledge}
              disabled={loading}
              className="rounded-xl bg-blue-600 px-6 py-3 font-semibold transition hover:bg-blue-500 disabled:cursor-not-allowed disabled:opacity-50"
            >
              {loading ? "Searching..." : "Search"}
            </button>
          </div>

          {/* Search results */}
          {results.length > 0 && (
            <div className="mt-8 space-y-4">
              <h3 className="text-lg font-semibold">
                Search Results
              </h3>

              {results.map((result, index) => (
                <div
                  key={`${result.source}-${result.chunk_id}-${index}`}
                  className="rounded-xl border border-slate-800 bg-slate-950 p-5"
                >
                  <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
                    <div>
                      <p className="text-sm font-medium text-blue-400">
                        {result.source || "No source"}
                      </p>

                      {result.chunk_id !== null && (
                        <p className="text-xs text-slate-500">
                          Chunk {result.chunk_id}
                        </p>
                      )}
                    </div>

                    <div className="rounded-lg bg-slate-800 px-3 py-1 text-xs text-slate-300">
                      Similarity:{" "}
                      {result.score.toFixed(3)}
                    </div>
                  </div>

                  <p className="mt-4 whitespace-pre-wrap text-sm leading-6 text-slate-300">
                    {result.text}
                  </p>
                </div>
              ))}
            </div>
          )}
        </section>

        {/* Upload */}
        <section className="mt-8 rounded-2xl border border-slate-800 bg-slate-900 p-6">
          <h2 className="text-xl font-semibold">
            Upload Document
          </h2>

          <p className="mt-1 text-sm text-slate-400">
            Upload a PDF to add it to your personal knowledge
            base.
          </p>

          <label className="mt-5 flex cursor-pointer flex-col items-center justify-center rounded-xl border border-dashed border-slate-700 bg-slate-950 p-8 text-center transition hover:border-blue-500">
            <span className="text-sm font-medium">
              {uploading
                ? "Uploading and indexing..."
                : "Choose a PDF file"}
            </span>

            <span className="mt-2 text-xs text-slate-500">
              PDF files only
            </span>

            <input
              type="file"
              accept=".pdf,application/pdf"
              onChange={uploadDocument}
              disabled={uploading}
              className="hidden"
            />
          </label>
        </section>

        {/* Documents */}
        <section className="mt-8 rounded-2xl border border-slate-800 bg-slate-900 p-6">
          <h2 className="text-xl font-semibold">
            My Documents
          </h2>

          {documents.length === 0 ? (
            <p className="mt-4 text-sm text-slate-500">
              No documents uploaded yet.
            </p>
          ) : (
            <div className="mt-5 space-y-3">
              {documents.map((document, index) => (
                <div
                  key={`${document.filename}-${index}`}
                  className="flex flex-col gap-2 rounded-xl border border-slate-800 bg-slate-950 p-4 sm:flex-row sm:items-center sm:justify-between"
                >
                  <div>
                    <p className="text-sm font-medium text-slate-200">
                      {document.filename}
                    </p>

                    <p className="mt-1 text-xs text-slate-500">
                      Uploaded{" "}
                      {new Date(
                        document.created_at
                      ).toLocaleString()}
                    </p>
                  </div>

                  <span className="text-xs text-emerald-400">
                    Indexed
                  </span>
                </div>
              ))}
            </div>
          )}
        </section>

        {/* Search History */}
        <section className="mt-8 rounded-2xl border border-slate-800 bg-slate-900 p-6">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-xl font-semibold">
                Recent Searches
              </h2>

              <p className="mt-1 text-sm text-slate-400">
                Your latest knowledge-base queries.
              </p>
            </div>
          </div>

          {history.length === 0 ? (
            <p className="mt-5 text-sm text-slate-500">
              No searches yet.
            </p>
          ) : (
            <div className="mt-5 space-y-3">
              {history.map((item, index) => (
                <div
                  key={`${item.query}-${item.created_at}-${index}`}
                  className="rounded-xl border border-slate-800 bg-slate-950 p-4"
                >
                  <p className="text-sm text-slate-200">
                    {item.query}
                  </p>

                  <p className="mt-1 text-xs text-slate-500">
                    {new Date(
                      item.created_at
                    ).toLocaleString()}
                  </p>
                </div>
              ))}
            </div>
          )}
        </section>

        {/* Footer */}
        <footer className="py-10 text-center text-xs text-slate-600">
          Personal Knowledge Base • FastAPI • Qdrant • MCP
        </footer>
      </div>
    </main>
  );
}