"""The server.

`gradio.Server` is a FastAPI app with Gradio's API engine bolted in. You get
queueing, streaming, and MCP for free, but you bring your own frontend. That
split is the point: the API is the product, the UI is disposable.
"""

import os
from pathlib import Path

from fastapi.responses import HTMLResponse
from gradio import Server

import assess
from llm import stream_reply
from schema import EvidenceDocument, Request, solve

app = Server()

FRONTEND = Path(__file__).parent / "frontend" / "index.html"

# --- The API -----------------------------------------------------------------
# The `-> str` return annotation is REQUIRED. Without it Gradio infers zero
# output components and silently returns nothing. Ask us how we know.

@app.api(name="chat")
def chat(message: str, history: list | None = None) -> str:  # type: ignore[misc]  # Gradio needs -> str on a generator
    """Stream a reply to one user message."""
    yield from stream_reply(message, history)


@app.api(name="propose_control_maturity")
def propose_control_maturity(control_id: str, evidence_documents: list[dict]) -> str:
    """Propose a maturity level for one control from the client's evidence documents.

    Returns a Response as JSON: verbatim quotes, a proposed level for documentation
    and for implementation (or no level when the evidence is not enough), any
    contradictions between documents, and the evidence still missing.

    Never makes the final decision; the consultant does.
    """
    # Validate the input against the contract in schema.py: a bad request stops here.
    request = Request(control_id=control_id, evidence_documents=[EvidenceDocument(**doc) for doc in evidence_documents])
    return solve(request).model_dump_json()


@app.api(name="assess_control_for_client")
def assess_control_for_client(client_id: str, control_id: str) -> str:
    """Assess one control for one client by finding the evidence in the client's own documents.

    Searches the client's documents (keyword and meaning search together), keeps the
    ones that support or contradict the control, and proposes a maturity level from
    them. Returns a Response as JSON: verbatim quotes checked against the documents,
    a proposed level for documentation and for implementation, contradictions, missing
    evidence, and `sources`, the record ids of the documents the assessment rests on.

    client_id is a client folder name, such as "klijent-01"; control_id is one of
    POL-001, ORG-001, EDU-001. An unknown client or control is an error, raised
    before any model call.

    When the search finds nothing usable (no documents, none that supports or
    contradicts the control, or no quote that is really in the documents), returns
    no level, an empty `sources` and the reason, instead of assessing from
    unrelated documents.

    Never makes the final decision; the consultant does.
    """
    return assess.assess_control_for_client(client_id, control_id).model_dump_json()

# --- The frontend ------------------------------------------------------------
# Defining a route at "/" replaces Gradio's default UI with ours.

@app.get("/", response_class=HTMLResponse)
def homepage() -> str:
    return FRONTEND.read_text(encoding="utf-8")


@app.get("/health")
def health() -> dict:
    """Your future ops team will thank you. Load balancers need this."""
    return {"status": "ok", "model": os.getenv("LLM_MODEL", "gpt-4.1-mini")}


if __name__ == "__main__":
    # 0.0.0.0 so the container is reachable from the host. On your laptop this
    # is fine. On a firm network, "reachable from where, exactly?" is the
    # question this challenge wants you to go ask.
    #
    # Read the port rather than hardcoding it, so a machine that already has
    # something on 7860 can move this one without editing code.
    port = int(os.getenv("GRADIO_SERVER_PORT", "7860"))

    # Gradio announces the address it BOUND to, which is 0.0.0.0 -- not an
    # address a browser can open. Windows rejects it outright; macOS and Linux
    # quietly redirect it to localhost, which is why it looks fine on some
    # machines and broken on others. Print the one that always works.
    print(f"\n  Open http://localhost:{port} in your browser\n", flush=True)
    app.launch(server_name="0.0.0.0", server_port=port)
