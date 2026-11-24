"""Assess one control for one client: retrieval in front of solve().

The steps:
1. Hybrid retrieval finds the client's documents that may be evidence.
2. One model call labels each of them: supports, contradicts or neutral.
3. No document supports or contradicts: the answer is "no relevant documents", and solve() is not called.
4. The supporting and contradicting documents go into the Week 1 Request and solve().
5. Every quote is checked against its document in code; a quote that is not there is dropped.
   No quote left: the answer is "no evidence", as in step 3.
6. The Response names the documents it came from in `sources`.

Week 7: every answer is written to memory as an episode (memory.py). Asked again with the same
documents, model and search, the stored answer comes back without a model call.
"""

import hashlib
import json
from typing import Literal

from pydantic import BaseModel

import memory
import retrieval
from llm import MODEL
from schema import CATALOG, DimensionAssessment, EvidenceDocument, Request, Response, _ask_model, solve


class DocumentLabel(BaseModel):
    record_id: str
    label: Literal["supports", "contradicts", "neutral"]
    reason: str


class DocumentLabels(BaseModel):
    documents: list[DocumentLabel]


class Explanation(BaseModel):
    text: str
    document_ids: list[str]
    citation_ids: list[str]


def find_candidates(client_id: str, control_id: str) -> dict[str, str]:
    """The documents the hybrid retrieval names for this control, by record id."""
    pages, _ = retrieval.load_client(client_id)
    tools, funcs = retrieval.hybrid_tools(pages, retrieval.embed_pages(pages))
    result = retrieval.run_agent(retrieval.task(control_id, CATALOG), tools, funcs)
    return {record_id: pages[record_id] for record_id in retrieval.found_documents(result["answer"], pages)}


def classify_documents(control_id: str, candidates: dict[str, str]) -> DocumentLabels:
    """One model call: does each document support the control, contradict it, or not bear on it?"""
    documents = "\n\n".join(f"[{record_id}]\n{text}" for record_id, text in candidates.items())
    prompt = (
        f"{retrieval.task(control_id, CATALOG)}\n\n"
        "For each document below, decide how it bears on this control:\n"
        "- supports: it shows the control is documented or implemented, even partly\n"
        "- contradicts: it shows the control is not in place, was withdrawn, or limited\n"
        "- neutral: it is about something else and does not change the assessment\n\n"
        f"DOCUMENTS:\n{documents}\n\n"
        'Reply with JSON only: {"documents": [{"record_id": "...", "label": "supports|contradicts|neutral", '
        '"reason": "one sentence"}]}, one entry per document.'
    )
    text = _ask_model(prompt).strip().removeprefix("```json").removeprefix("```").removesuffix("```")
    return DocumentLabels.model_validate_json(text)


def decline_response(control_id: str, reason: str) -> Response:
    """A Response with no level, saying why: a decline is a valid answer."""
    no_level = DimensionAssessment(low_confidence=False, uncertainty_reason=reason, rationale=reason)
    return Response(control_id=control_id, documentation=no_level, implementation=no_level.model_copy(),
                    missing_evidence=["Dokumenti koji dokazuju ovu kontrolu."])


def to_document(record_id: str, page: str) -> EvidenceDocument:
    """A client page as the Week 1 EvidenceDocument: the heading is the name, the rest is the content."""
    heading, _, content = page.partition("\n")
    return EvidenceDocument(document_id=record_id, name=heading.removeprefix("# ").strip(), content=content.strip())


def verify_citations(response: Response, documents: list[EvidenceDocument]) -> list[str]:
    """Drop every quote that is not word for word in its document; return the ids of the dropped ones."""
    texts = {doc.document_id: " ".join(doc.content.split()) for doc in documents}
    kept, dropped = [], []
    for citation in response.citations:
        if " ".join(citation.text.split()) in texts.get(citation.document_id, ""):
            kept.append(citation)
        else:
            dropped.append(citation.citation_id)
    response.citations = kept
    for dimension in (response.documentation, response.implementation):
        lost = [cid for cid in dimension.citation_ids if cid in dropped]
        if lost:
            dimension.citation_ids = [cid for cid in dimension.citation_ids if cid not in dropped]
            # The level stays for the consultant to see, but it no longer rests on everything it cited.
            dimension.low_confidence = dimension.level is not None
            note = f"Citati {', '.join(lost)} nisu nađeni doslovno u dokumentu i uklonjeni su."
            dimension.uncertainty_reason = f"{dimension.uncertainty_reason} {note}".strip() if dimension.uncertainty_reason else note
    return dropped


def inputs_hash(client_id: str, find) -> str:
    """What the answer depends on: the client's documents, the model and which search ran."""
    pages, _ = retrieval.load_client(client_id)
    documents = "\n".join(f"{record_id}\n{pages[record_id]}" for record_id in sorted(pages))
    return hashlib.sha256(f"{MODEL}\n{find.__name__}\n{documents}".encode()).hexdigest()


def assess_control_for_client(client_id: str, control_id: str, find=find_candidates) -> Response:
    """Assess one control for one client, or return the stored answer if nothing it depends on changed.

    `find` is the search, passed in so TC5 can swap in the skill and count either one.
    """
    if control_id not in CATALOG:
        raise ValueError(f"Unknown control: {control_id}")
    key = inputs_hash(client_id, find)
    stored = memory.live(client_id, control_id, "assessment")
    if stored and stored["inputs_hash"] == key:
        return Response.model_validate(stored["data"]["response"])

    episode = {"model": MODEL, "search": find.__name__}
    response = run_assessment(client_id, control_id, find, episode)
    episode["response"] = response.model_dump()
    # An error raises before this line and is not kept. A decline is kept, even one from a search
    # that ran out of turns, until a document, the model or the search changes.
    memory.record(client_id, control_id, "assessment", episode, inputs_hash=key)
    return response


def run_assessment(client_id: str, control_id: str, find, episode: dict) -> Response:
    """Retrieve, classify, assess and check, writing down in `episode` what each step did."""
    candidates = find(client_id, control_id)
    episode["found"] = list(candidates)
    if not candidates:
        episode["outcome"] = "no documents found"
        return decline_response(control_id, "Pretraga nije našla nijedan dokument za ovu kontrolu.")

    labels = classify_documents(control_id, candidates)
    episode["labels"] = [label.model_dump() for label in labels.documents]
    relevant = [d.record_id for d in labels.documents if d.label != "neutral" and d.record_id in candidates]
    episode["relevant"] = relevant
    if not relevant:
        episode["outcome"] = "no relevant documents"
        return decline_response(control_id, "Nijedan nađeni dokument ne potvrđuje ni ne osporava ovu kontrolu.")

    documents = [to_document(record_id, candidates[record_id]) for record_id in relevant]
    response = solve(Request(control_id=control_id, evidence_documents=documents))
    episode["dropped_citations"] = verify_citations(response, documents)
    if response.documentation.level is None and response.implementation.level is None:
        # Any reply with no level (a decline, or a document the guardrails stopped) keeps its own reason and has no sources.
        episode["outcome"] = "no level"
        return response
    if not response.citations:
        episode["outcome"] = "no quote found word for word"
        return decline_response(control_id, "Nijedan citat nije nađen doslovno u dokumentima.")
    response.sources = relevant
    episode["outcome"] = "assessed"
    return response


def explain(client_id: str, control_id: str) -> Explanation:
    """Why the tool answered as it did, from the stored episode and the consultant's decisions.

    The model gets the log and has to name the documents and quotes it uses, so a test can check
    each one against the log.
    """
    episode = memory.live(client_id, control_id, "assessment")
    if not episode:
        return Explanation(text="Nema zapisa o procjeni ove kontrole za ovog klijenta.", document_ids=[], citation_ids=[])
    # A decision older than this assessment was about an earlier answer, so it is left out.
    decisions = [d["data"] for dimension in ("documentation", "implementation")
                 if (d := memory.live(client_id, control_id, "decision", dimension))
                 and d["created_at"] >= episode["created_at"]]
    prompt = (
        f"Below is the log of one assessment of control {control_id}: the documents the search found, "
        "how each was labelled, the quotes the check dropped, and the answer given. "
        "After it come the consultant's decisions on that answer, if there are any.\n\n"
        "Explain to the consultant why the tool gave this answer. Use only what is in the log. "
        "Do not mention a document, quote or step that is not in it. Write in Croatian.\n\n"
        f"LOG:\n{json.dumps(episode['data'], ensure_ascii=False)}\n\n"
        f"DECISIONS:\n{json.dumps(decisions, ensure_ascii=False) if decisions else 'none'}\n\n"
        'Reply with JSON only: {"text": "...", "document_ids": ["..."], "citation_ids": ["..."]}, '
        "listing the document record ids and citation ids your explanation relies on."
    )
    text = _ask_model(prompt).strip().removeprefix("```json").removeprefix("```").removesuffix("```")
    return Explanation.model_validate_json(text)


if __name__ == "__main__":
    import sys

    print(assess_control_for_client(sys.argv[1], sys.argv[2]).model_dump_json(indent=2))
