"""Assess one control for one client: retrieval in front of solve().

The steps:
1. Hybrid retrieval finds the client's documents that may be evidence.
2. One model call labels each of them: supports, contradicts or neutral.
3. No document supports or contradicts: the answer is "no relevant documents", and solve() is not called.
4. The supporting and contradicting documents go into the Week 1 Request and solve().
5. Every quote is checked against its document in code; a quote that is not there is dropped.
6. The Response names the documents it came from in `sources`.
"""

import json
from typing import Literal

from pydantic import BaseModel

import retrieval
from llm import stream_reply
from schema import CATALOG, DimensionAssessment, EvidenceDocument, Request, Response, solve


class DocumentLabel(BaseModel):
    record_id: str
    label: Literal["supports", "contradicts", "neutral"]
    reason: str


class DocumentLabels(BaseModel):
    documents: list[DocumentLabel]


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
    reply = ""
    for text_so_far in stream_reply(prompt):
        reply = text_so_far
    text = reply.strip().removeprefix("```json").removeprefix("```").removesuffix("```")
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


def assess_control_for_client(client_id: str, control_id: str) -> Response:
    """Retrieve, classify, assess and check one control for one client."""
    candidates = find_candidates(client_id, control_id)
    if not candidates:
        return decline_response(control_id, "Pretraga nije našla nijedan dokument za ovu kontrolu.")

    labels = classify_documents(control_id, candidates)
    relevant = [d.record_id for d in labels.documents if d.label != "neutral" and d.record_id in candidates]
    if not relevant:
        return decline_response(control_id, "Nijedan nađeni dokument ne potvrđuje ni ne osporava ovu kontrolu.")

    documents = [to_document(record_id, candidates[record_id]) for record_id in relevant]
    response = solve(Request(control_id=control_id, evidence_documents=documents))
    verify_citations(response, documents)
    if not response.citations:
        return decline_response(control_id, "Nijedan citat nije nađen doslovno u dokumentima.")
    response.sources = relevant
    return response


if __name__ == "__main__":
    import sys

    print(assess_control_for_client(sys.argv[1], sys.argv[2]).model_dump_json(indent=2))
