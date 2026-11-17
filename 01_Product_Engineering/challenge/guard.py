"""Week 6: the client's documents pass the guardrails before the assessment reads them.

The documents are the untrusted input of this app: the client and its staff write them, and
the assessment cannot work without them, so that leg cannot be removed. What can be checked is
that a document does not talk to the system reading it (guardrails/config.yml).

Fail closed: if the rails themselves fail, the document counts as stopped. A guardrail that lets
everything through when it breaks switches itself off exactly when nobody is looking.
"""

from pathlib import Path

from nemoguardrails import LLMRails, RailsConfig

RAILS = LLMRails(RailsConfig.from_path(str(Path(__file__).parent / "guardrails")))

# Input rails only: no dialog, no model call, the documents are checked, not answered.
OPTIONS = {"rails": {"input": True, "dialog": False, "output": False, "retrieval": False},
           "log": {"activated_rails": True}}


def stopped_by(text: str) -> str | None:
    """The rung that stopped this text, or None when it passes every rung."""
    try:
        response = RAILS.generate(messages=[{"role": "user", "content": text}], options=OPTIONS)
    except Exception as error:
        return f"rails failed ({type(error).__name__})"
    return next((rail.name for rail in response.log.activated_rails if rail.stop), None)


def stopped_documents(documents) -> dict[str, str]:
    """Document id -> the rung that stopped it, for every document that does not pass."""
    stopped = {}
    for document in documents:
        rung = stopped_by(f"{document.name}\n{document.content}")
        if rung:
            stopped[document.document_id] = rung
    return stopped
