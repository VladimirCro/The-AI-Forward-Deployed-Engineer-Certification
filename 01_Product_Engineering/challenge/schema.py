from pydantic import BaseModel, Field

class EvidenceDocument(BaseModel):
    """Evidence document from the customer."""
    document_id: str = Field(description="Document ID, e.g., DOC-01")
    name: str = Field(description="Document name")
    content: str = Field(description="Document content")

class Request(BaseModel):
    """One control to assess, with its evidence documents."""
    control_id: str = Field(description="Control ID from the catalog, e.g. POL-001")
    evidence_documents: list[EvidenceDocument] = Field(min_length=1, description="List of evidence documents")

class Citation(BaseModel):
    """A citation within an evidence document."""
    citation_id: str = Field(description="Citation ID from the tool, e.g. CIT-01")
    document_id: str = Field(description="Document ID from the document list, e.g. DOC-01")
    location: str = Field(description="Location within the document, e.g., page 3, paragraph 2")
    text: str = Field(description="Word for word, no paraphrasing, what the document says at that location") 

class DimensionAssessment(BaseModel):
    """Assessment of a single dimension of a control."""
    level: int | None = Field(default=None, ge =1, le = 5, description="Level of maturity, 1-5, or null if not enough evidence to assess")
    level_statement: str | None = Field(default=None, description="Description of the level, from the catalog control description")
    low_confidence: bool = Field(description="True if the model is not confident in the level it proposed; contradictions between documents go in contradictions, not here")
    uncertainty_reason: str | None = Field(default=None, description="Explain why there is no level or why it is low confidence")
    rationale: str = Field(description="Rationale for the assessment, exactly why this level was chosen, and why it is not a different level")
    citation_ids: list[str] = Field(default_factory=list, description="List of citation IDs that support this assessment")

class Response(BaseModel):
    """Response to the assessment request, including the assessment of each dimension and any contradictions or missing evidence."""
    control_id: str = Field(description="The control this assessment is for")
    citations: list[Citation] = Field(default_factory=list, description="List of citations found in the evidence documents")
    documentation: DimensionAssessment = Field(description="documentation assessment grade")
    implementation: DimensionAssessment = Field(description="implementation assessment grade")
    contradictions: list[str] = Field(default_factory=list, description="List of contradictions found in the evidence documents")
    missing_evidence: list[str] = Field(default_factory=list, description="List of missing evidence that would be needed to make a confident assessment")

def solve(request: Request) -> Response:
    """Assess one control against the client's evidence documents.

    Sends the control and the documents to the model and returns a Response with
    the cited quotes, a proposed level for documentation and for implementation,
    any contradictions between documents, and the evidence still missing for a
    confident assessment.

    Never makes the final decision; the consultant does, after reviewing the Response.
    """
    raise NotImplementedError("implement against this signature")