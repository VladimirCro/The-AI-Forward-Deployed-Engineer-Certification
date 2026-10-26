"""Retrieval over one client's documents: the techniques Week 3 measures.

A client is a folder of pages, one page per document, named by its record id
(use_case/data/clients/klijent-01/r12-DOC-07.md), plus index.md. Every technique
runs over the same pages, so a difference in the results comes from the technique.

The tools and the agent loop are lifted from Session 5
(03_Retrieval/sessions/S5_Agentic_Retrieval.py); the comments say where they differ.
"""

import json
import os
import re
import time
from pathlib import Path

from rank_bm25 import BM25Okapi

from llm import chat_with_tools

CLIENTS_DIR = Path(os.getenv("CLIENTS_DIR", Path(__file__).resolve().parents[2] / "use_case" / "data" / "clients"))
MAX_TURNS = 6
TOP_K = 4  # the largest gold list has four documents

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


def tool_schema(name: str, description: str, properties: dict, required: tuple = ()) -> dict:
    """A tool as the model sees it: name, description and arguments."""
    return {"type": "function", "function": {"name": name, "description": description,
            "parameters": {"type": "object", "properties": properties, "required": list(required)}}}


def rag_tools(pages: dict[str, str]) -> tuple[list[dict], dict]:
    """Agentic RAG: one BM25 search over the pages, which the model may call again with a new query."""
    # Session 5 split pages at ## headings; ours have one heading each, so one page is one chunk.
    record_ids = list(pages)
    bm25 = BM25Okapi([tokenize(pages[record_id]) for record_id in record_ids])

    def search_chunks(query: str, k: int = TOP_K) -> str:
        scores = bm25.get_scores(tokenize(query))
        ranked = sorted(range(len(record_ids)), key=lambda n: scores[n], reverse=True)
        results = []
        for n in ranked[: max(1, min(k, 8))]:
            results.append(f"[{record_ids[n]}]\n{pages[record_ids[n]][:1000]}")
        return "\n\n---\n\n".join(results)

    tools = [tool_schema("search_chunks", "Search ranked document chunks. Search again with a new query when evidence is incomplete.",
                         {"query": {"type": "string"}, "k": {"type": "integer"}}, ("query",))]
    return tools, {"search_chunks": search_chunks}


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
