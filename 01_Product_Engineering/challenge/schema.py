import json
from pathlib import Path

from pydantic import BaseModel, Field

from llm import stream_reply

CATALOG = json.loads((Path(__file__).parent / "catalog.json").read_text(encoding="utf-8"))

class EvidenceDocument(BaseModel):
    """Evidence document from the customer."""
    document_id: str = Field(description="Document ID, e.g., DOC-01")
    name: str = Field(description="Document title as the client calls it, such as 'Information security policy, version 0.9' or 'Minutes of the 7th board meeting'")
    content: str = Field(description="Full text of the document as written, not a summary. Quotes are copied from this text")

class Request(BaseModel):
    """One control to assess, with its evidence documents."""
    control_id: str = Field(description="Control ID from the catalog, e.g. POL-001")
    evidence_documents: list[EvidenceDocument] = Field(min_length=1, description="Documents the client gave as evidence for this control, such as a policy, board minutes, a rulebook or a training report")

class Citation(BaseModel):
    """A citation within an evidence document."""
    citation_id: str = Field(description="Citation ID from the tool, e.g. CIT-01")
    document_id: str = Field(description="Document ID from the document list, e.g. DOC-01")
    location: str = Field(description="Location within the document, e.g., page 3, paragraph 2")
    text: str = Field(description="Word for word, no paraphrasing, what the document says at that location") 

class DimensionAssessment(BaseModel):
    """Assessment of a single dimension of a control."""
    level: int | None = Field(default=None, ge=1, le=5, description="Level of maturity, 1-5, or null if not enough evidence to assess")
    level_statement: str | None = Field(default=None, description="The catalog statement for the chosen level, filled in by the tool. The model leaves it null")
    low_confidence: bool = Field(description="True if a level is given but the model is not confident in it; false when there is no level. Contradictions between documents go in contradictions, not here")
    uncertainty_reason: str | None = Field(default=None, description="Why there is no level, or why the level is uncertain, such as 'the only document is an IT strategy and does not cover the security policy'")
    rationale: str = Field(description="Rationale for the assessment, exactly why this level was chosen, and why it is not a different level")
    citation_ids: list[str] = Field(default_factory=list, description="IDs from citations that support this level, such as ['CIT-01', 'CIT-03']")

class Response(BaseModel):
    """Response to the assessment request, including the assessment of each dimension and any contradictions or missing evidence."""
    control_id: str = Field(description="The control this assessment is for, the same as in the request, such as POL-001")
    citations: list[Citation] = Field(default_factory=list, description="Word-for-word quotes from the evidence documents, each with its document and location. Each dimension refers to them by citation_id")
    documentation: DimensionAssessment = Field(description="Maturity of the documentation: does the document exist, is it complete and formally approved")
    implementation: DimensionAssessment = Field(description="Maturity of the implementation: is it done in practice, such as adopted by the board and applied in the organisation's processes")
    contradictions: list[str] = Field(default_factory=list, description="Places where documents disagree, one per item, such as 'The intranet post (DOC-03) says the policy was adopted, the board minutes (DOC-02) say adoption was postponed'")
    missing_evidence: list[str] = Field(default_factory=list, description="Evidence to ask the client for before a confident assessment, one per item, such as 'Board decision adopting the policy'")

def _control(control_id: str) -> dict:
    """The control's scale from the catalog: five statements for documentation, five for implementation."""
    if control_id not in CATALOG:
        raise ValueError(f"Unknown control: {control_id}")
    return CATALOG[control_id]

def _build_prompt(request: Request, control: dict) -> str:
    """The prompt in four blocks: task, scale, documents, rules."""
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

    return "\n\n".join([task, scale, documents, rules])

def _ask_model(prompt: str) -> str:
    """The model's full reply. stream_reply yields the text so far, so the last one is the whole reply."""
    reply = ""
    for text_so_far in stream_reply(prompt):
        reply = text_so_far
    return reply

def _parse(reply: str) -> Response:
    """Check the reply against Response. A reply that doesn't match fails here instead of reaching the consultant."""
    # The model often wraps its JSON in a ```json fence.
    text = reply.strip().removeprefix("```json").removeprefix("```").removesuffix("```")
    return Response.model_validate_json(text)

def _fill_level_statements(response: Response, control: dict) -> None:
    """Fill in the regulator's exact statement for each proposed level."""
    pairs = [
        (response.documentation, control["documentation"]),
        (response.implementation, control["implementation"]),
    ]
    for dimension, statements in pairs:
        if dimension.level is not None:
            # Catalog keys are strings ("1" to "5"); level is an int.
            dimension.level_statement = statements[str(dimension.level)]
    
def solve(request: Request) -> Response:
    """Assess one control against the client's evidence documents.

    Sends the control and the documents to the model and returns a Response with
    the cited quotes, a proposed level for documentation and for implementation,
    any contradictions between documents, and the evidence still missing for a
    confident assessment.

    Never makes the final decision; the consultant does, after reviewing the Response.
    """
    # 1. The control's scale from the catalog; an unknown control stops here.
    control = _control(request.control_id)
    # 2. One prompt: task, scale, documents, rules.
    prompt = _build_prompt(request, control)
    # 3. The model's full reply.
    reply = _ask_model(prompt)
    # 4. Check it against the contract.
    response = _parse(reply)
    # 5. The level statements come from the catalog, not from the model.
    _fill_level_statements(response, control)
    return response