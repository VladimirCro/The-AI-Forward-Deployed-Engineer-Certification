"""Retrieval over one client's documents: the techniques Week 3 measures.

A client is a folder of pages, one page per document, named by its record id
(use_case/data/clients/klijent-01/r12-DOC-07.md), plus index.md. Every technique
runs over the same pages, so a difference in the results comes from the technique.

The tools and the agent loop are lifted from Session 5
(03_Retrieval/sessions/S5_Agentic_Retrieval.py), the embedder and the rank fusion
from Session 6 (S6_Multimodal_Retrieval.py); the comments say where they differ.
"""

import json
import os
import re
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import numpy as np
from litellm import embedding
from rank_bm25 import BM25Okapi

from llm import chat_with_tools

# `or`, not a getenv default: the repo path does not exist inside the container, and a
# default argument is worked out even when CLIENTS_DIR is set.
CLIENTS_DIR = Path(os.getenv("CLIENTS_DIR") or Path(__file__).resolve().parents[2] / "use_case" / "data" / "clients")
MAX_TURNS = 6
TOP_K = 4  # the largest gold list has four documents
RRF_K = 60  # Session 6's default
FIRST_STAGE = 50  # how far down each ranking goes before the fusion

EMBED_MODEL = os.getenv("EMBED_MODEL", "openai/gemini-embedding-2")
EMBED_API_BASE = os.getenv("EMBED_API_BASE")  # the gateway's embedding route is not the chat one
EMBED_WORKERS = 8

# Session 5 split words with [a-z0-9£$%]+, which drops č, ć, š, ž and đ from Croatian words.
WORD = re.compile(r"\w+")

SYSTEM = (
    "You find the evidence for one control in one client's documents. "
    "Use only what the tools return. Investigate before answering. "
    "For every document that is evidence, give its record id in square brackets, like [r12-DOC-07], "
    "and quote what it says. If no document is evidence for the control, say: no evidence found."
)


def load_client(client_id: str) -> tuple[dict[str, str], str]:
    """The client's pages by record id, and its index page."""
    folder = CLIENTS_DIR / client_id
    if not folder.is_dir():
        raise ValueError(f"Unknown client: {client_id}")
    pages = {}
    for path in sorted(folder.glob("r*.md")):
        pages[path.stem] = path.read_text(encoding="utf-8")
    index = (folder / "index.md").read_text(encoding="utf-8")
    return pages, index


def task(control_id: str, catalog: dict) -> str:
    """The request the retrieval gets: the control and what its levels ask for, from the catalog."""
    control = catalog[control_id]
    lines = [f"Control {control_id}: {control['name']}", "", "Implementation levels:"]
    for level, text in control["implementation"].items():
        lines.append(f"{level}: {text}")
    lines.append("")
    lines.append("Find every document among this client's documents that is evidence for this control.")
    return "\n".join(lines)


def tokenize(text: str) -> list[str]:
    """Lower-case words, Croatian letters included."""
    return WORD.findall(text.lower())


class TextEmbedder:
    """Text in, unit vectors out, through LiteLLM's embedding(); counts the tokens the endpoint reports.

    Lifted from Session 6, without its local fallback: the model download is blocked on
    the firm network, so a local model is not a path here.
    """

    def __init__(self):
        if not EMBED_API_BASE:
            # Without it LiteLLM sends the gateway key to the provider's public API.
            raise RuntimeError("EMBED_API_BASE is not set")
        self.model_id = EMBED_MODEL
        self.tokens = 0
        self.lock = threading.Lock()

    def embed_one(self, text: str) -> list[float]:
        """One text, one call: the gateway merges a list of texts into a single vector."""
        response = embedding(model=EMBED_MODEL, input=[text], api_base=EMBED_API_BASE, timeout=120)
        with self.lock:
            self.tokens += int(getattr(response.usage, "total_tokens", 0) or 0)
        return response.data[0]["embedding"]

    def embed(self, texts: list[str]) -> np.ndarray:
        """Unit vectors for the texts, in their order."""
        with ThreadPoolExecutor(max_workers=EMBED_WORKERS) as pool:
            return unit_vectors(list(pool.map(self.embed_one, texts)))


def unit_vectors(vectors) -> np.ndarray:
    """Unit length, so a dot product is the cosine."""
    matrix = np.asarray(vectors, dtype="float32")
    return matrix / (np.linalg.norm(matrix, axis=-1, keepdims=True) + 1e-9)


EMBEDDER = TextEmbedder()


def embed_pages(pages: dict[str, str]) -> np.ndarray:
    """One vector per page, in the order of the pages."""
    return EMBEDDER.embed(list(pages.values()))


def tool_schema(name: str, description: str, properties: dict, required: tuple = ()) -> dict:
    """A tool as the model sees it: name, description and arguments."""
    return {"type": "function", "function": {"name": name, "description": description,
            "parameters": {"type": "object", "properties": properties, "required": list(required)}}}


def bm25_ranking(pages: dict[str, str]):
    """A function from a query to every record id, best BM25 match first."""
    # Session 5 split pages at ## headings; ours have one heading each, so one page is one chunk.
    record_ids = list(pages)
    bm25 = BM25Okapi([tokenize(pages[record_id]) for record_id in record_ids])

    def rank(query: str) -> list[str]:
        scores = bm25.get_scores(tokenize(query))
        order = sorted(range(len(record_ids)), key=lambda n: scores[n], reverse=True)
        return [record_ids[n] for n in order]

    return rank


def dense_ranking(pages: dict[str, str], vectors: np.ndarray):
    """A function from a query to every record id, closest in meaning first (cosine)."""
    record_ids = list(pages)

    def rank(query: str) -> list[str]:
        scores = vectors @ EMBEDDER.embed([query])[0]
        order = sorted(range(len(record_ids)), key=lambda n: scores[n], reverse=True)
        return [record_ids[n] for n in order]

    return rank


def reciprocal_rank_fusion(rankings: list[list[str]], k: int = RRF_K) -> list[str]:
    """Merge ranked lists by rank, not by score, as Session 6 does: BM25 and cosine scores do not compare."""
    fused = {}
    for ranking in rankings:
        for rank, record_id in enumerate(ranking):
            fused[record_id] = fused.get(record_id, 0.0) + 1.0 / (k + rank + 1)
    return sorted(fused, key=fused.get, reverse=True)


def search_tool(pages: dict[str, str], rank) -> tuple[list[dict], dict]:
    """The one search_chunks tool over any ranking, so the techniques differ only in how they rank."""

    def search_chunks(query: str, k: int = TOP_K) -> str:
        results = []
        for record_id in rank(query)[: max(1, min(k, 8))]:
            results.append(f"[{record_id}]\n{pages[record_id][:1000]}")
        return "\n\n---\n\n".join(results)

    tools = [tool_schema("search_chunks", "Search ranked document chunks. Search again with a new query when evidence is incomplete.",
                         {"query": {"type": "string"}, "k": {"type": "integer"}}, ("query",))]
    return tools, {"search_chunks": search_chunks}


def rag_tools(pages: dict[str, str]) -> tuple[list[dict], dict]:
    """Agentic RAG: one BM25 search over the pages, which the model may call again with a new query."""
    return search_tool(pages, bm25_ranking(pages))


def dense_tools(pages: dict[str, str], vectors: np.ndarray) -> tuple[list[dict], dict]:
    """Dense: the same search tool, ranked by embedding similarity instead of BM25."""
    return search_tool(pages, dense_ranking(pages, vectors))


def hybrid_tools(pages: dict[str, str], vectors: np.ndarray) -> tuple[list[dict], dict]:
    """Hybrid: the same search tool, BM25 and dense rankings merged with reciprocal rank fusion."""
    bm25, dense = bm25_ranking(pages), dense_ranking(pages, vectors)

    def rank(query: str) -> list[str]:
        return reciprocal_rank_fusion([bm25(query)[:FIRST_STAGE], dense(query)[:FIRST_STAGE]])

    return search_tool(pages, rank)


def dci_tools(pages: dict[str, str], index: str) -> tuple[list[dict], dict]:
    """Direct corpus interaction: list the pages, grep across them, read one whole."""

    def list_pages() -> str:
        return index

    def grep_wiki(pattern: str) -> str:
        try:
            rx = re.compile(pattern, re.I)
        except re.error:
            rx = re.compile(re.escape(pattern), re.I)
        hits = []
        for record_id, text in pages.items():
            for number, line in enumerate(text.splitlines(), 1):
                if rx.search(line):
                    hits.append(f"{record_id}:{number}: {line}")
        return "\n".join(hits[:40]) or "(no matches)"

    def read_page(page: str) -> str:
        if page not in pages:
            return f"(unknown page: {page})"
        return pages[page][:12000]

    tools = [
        tool_schema("list_pages", "Read the index of the client's documents.", {}),
        tool_schema("grep_wiki", "Search exact text or a regular expression across the documents, with the record id and line.",
                    {"pattern": {"type": "string"}}, ("pattern",)),
        tool_schema("read_page", "Read one whole document by its record id.",
                    {"page": {"type": "string", "enum": sorted(pages)}}, ("page",)),
    ]
    return tools, {"list_pages": list_pages, "grep_wiki": grep_wiki, "read_page": read_page}


def run_agent(question: str, tools: list[dict], funcs: dict, max_turns: int = MAX_TURNS) -> dict:
    """The tool loop from Session 5: the model calls tools until it answers or runs out of turns."""
    messages = [{"role": "system", "content": SYSTEM}, {"role": "user", "content": question}]
    trace, chars = [], 0
    started = time.perf_counter()
    for _ in range(max_turns):
        msg = chat_with_tools(messages, tools)
        calls = msg.tool_calls or []
        if not calls:
            return {"answer": (msg.content or "").strip(), "trace": trace, "evidence_chars": chars,
                    "latency_s": time.perf_counter() - started, "stopped": "answer"}
        shaped = [{"id": call.id, "type": "function",
                   "function": {"name": call.function.name, "arguments": call.function.arguments}} for call in calls]
        messages.append({"role": "assistant", "content": msg.content or "", "tool_calls": shaped})
        for call in shaped:
            name = call["function"]["name"]
            args = {}  # Session 5 left this unset, so a bad argument string crashed the trace line
            try:
                args = json.loads(call["function"]["arguments"] or "{}")
                if name not in funcs:
                    raise KeyError(f"unknown tool {name}")
                result = str(funcs[name](**args))
            except Exception as exc:
                result = f"(tool error: {type(exc).__name__}: {exc})"
            chars += len(result)
            trace.append({"tool": name, "args": args, "chars": len(result)})
            messages.append({"role": "tool", "tool_call_id": call["id"], "content": result})
    return {"answer": "(max turns reached)", "trace": trace, "evidence_chars": chars,
            "latency_s": time.perf_counter() - started, "stopped": "max_turns"}


def found_documents(answer: str, pages: dict[str, str]) -> list[str]:
    """Record ids the answer names that exist for this client: the sources."""
    found = []
    for record_id in re.findall(r"r\d+-DOC-\d+", answer):
        if record_id in pages and record_id not in found:
            found.append(record_id)
    return found
