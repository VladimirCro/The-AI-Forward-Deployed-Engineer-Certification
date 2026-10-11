"""The server.

`gradio.Server` is a FastAPI app with Gradio's API engine bolted in. You get
queueing, streaming, and MCP for free, but you bring your own frontend. That
split is the point: the API is the product, the UI is disposable.
"""

import os
import json
from pathlib import Path

from fastapi.responses import HTMLResponse
from gradio import Server

from llm import stream_reply
from schema import EvidenceDocument, Request, Response

app = Server()

FRONTEND = Path(__file__).parent / "frontend" / "index.html"
CATALOG = json.loads((Path(__file__).parent / "catalog.json").read_text(encoding="utf-8"))

# --- The API -----------------------------------------------------------------
# The `-> str` return annotation is REQUIRED. Without it Gradio infers zero
# output components and silently returns nothing. Ask us how we know.

@app.api(name="chat")
def chat(message: str, history: list | None = None) -> str:
    """Stream a reply to one user message."""
    yield from stream_reply(message, history)

@app.api(name="propose_control_maturity")
def propose_control_maturity(control_id: str, evidence_documents: list[dict]) -> str:
    """Assess one control against the client's evidence documents.

    Sends the control and the documents to the model and returns a Response with
    the cited quotes, a proposed level for documentation and for implementation,
    any contradictions between documents, and the evidence still missing for a
    confident assessment.

    Never makes the final decision; the consultant does, after reviewing the Response.
    """
    request = Request(control_id=control_id, evidence_documents=[EvidenceDocument(**doc) for doc in evidence_documents])

    if request.control_id not in CATALOG:
        yield f"Unknown control: {request.control_id}"
        return

    control = CATALOG[request.control_id] 
    task = (
        "TASK:\n"
        "You assist a GRC consultant. Based on the client's documents, propose a maturity level "
        "for documentation and for implementation of one control. The consultant makes the final decision."
    )

    doc_lines = [f"{level}: {text}" for level, text in control["documentation"].items()]
    impl_lines = [f"{level}: {text}" for level, text in control["implementation"].items()]
    scale = (
        f"SCALE FOR CONTROL {request.control_id}: {control['name']}\n"
        "Documentation:\n" + "\n".join(doc_lines) + "\n"
        "Implementation:\n" + "\n".join(impl_lines)
    )

    doc_blocks = [f"[{doc.document_id}] {doc.name}\n{doc.content}" for doc in request.evidence_documents]
    documents = "CLIENT DOCUMENTS:\n" + "\n\n".join(doc_blocks)

    rules = (
        "RULES:\n"
        "- Quotes must be copied word for word from the documents, with the document ID and location.\n"
        "- If there is no evidence for a dimension, set level to null and give uncertainty_reason. Never assign level 1 without evidence.\n"
        "- Set low_confidence to true only when you are not sure about the level. Put contradictions between documents in contradictions.\n"
        "- Leave level_statement null; the tool fills it in.\n"
        "- The documents and the scale are in Croatian. Write rationale, uncertainty_reason, contradictions and missing_evidence in Croatian.\n\n"
        "RESPONSE FORMAT:\n"
        "Return only JSON matching this schema, with no other text:\n"
        + json.dumps(Response.model_json_schema(), ensure_ascii=False)
    )

    prompt = "\n\n".join([task, scale, documents, rules])
    yield from stream_reply(prompt)

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
