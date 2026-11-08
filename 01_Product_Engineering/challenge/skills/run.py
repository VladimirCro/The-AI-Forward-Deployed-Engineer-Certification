"""Search one client's documents: python run.py klijent-01 "odluka uprave o usvajanju politike"

Prints the top documents for the query, the same text the search tool returns in
the Week 3 endpoint. The skill runs this as a subprocess, so no counter in the
calling process sees it: each run appends one line to SKILL_CALL_LOG when it is set.
"""

import hashlib
import json
import os
import sys
import tempfile
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import retrieval

# Every run is a new process, so without this each query would embed all 150 pages again.
VECTORS_DIR = Path(os.getenv("VECTORS_DIR") or Path(tempfile.gettempdir()) / "skill-vectors")


def client_vectors(client_id: str, pages: dict[str, str]) -> np.ndarray:
    """The client's page vectors, embedded once and kept by a hash of the pages."""
    digest = hashlib.sha256("\n".join(f"{rid}\n{text}" for rid, text in pages.items()).encode("utf-8")).hexdigest()[:16]
    path = VECTORS_DIR / f"{client_id}-{digest}.npy"
    if path.exists():
        return np.load(path)
    vectors = retrieval.embed_pages(pages)
    VECTORS_DIR.mkdir(parents=True, exist_ok=True)
    np.save(path, vectors)
    return vectors


def main() -> None:
    client_id, query = sys.argv[1], " ".join(sys.argv[2:])
    pages, _ = retrieval.load_client(client_id)
    _, funcs = retrieval.hybrid_tools(pages, client_vectors(client_id, pages))
    result = funcs["search_chunks"](query)
    log = os.getenv("SKILL_CALL_LOG")
    if log:
        with open(log, "a", encoding="utf-8") as f:
            f.write(json.dumps({"client": client_id, "query": query, "bytes": len(result.encode("utf-8"))}, ensure_ascii=False) + "\n")
    print(result)


if __name__ == "__main__":
    main()
