"""Variation axes for the TC2 synthetic data."""

AXES = {
    "control": {
        "POL-001": "Top-level cybersecurity policy: does it exist and is it formally adopted by the board",
        "ORG-001": "Roles, responsibilities and duties: are they assigned, documented and communicated",
        "EDU-001": "Staff awareness: are employees trained on the key points of the policy",
    },
    "document_state": [
        "adopted and in force",
        "draft",
        "not adopted or not signed",
        "incomplete (a section or annex is missing)",
        "badly or vaguely worded",
        "outdated (adopted, but not reviewed for years)",
    ],
    "document_relation": [
        "documents agree",
        "documents contradict each other",
        "several versions of the same document",
        "a later event changes the situation",
        "refers to a document that was not submitted",
    ],
    "implementation_evidence": [
        "full evidence",
        "partial evidence, near a level threshold",
        "paper only, no evidence of implementation",
        "evidence only, no paper",
        "irrelevant documents only (decline: no level, ask for evidence)",
    ],
}

AXIS_REASONS = {
    "control": "The system must work on every topic, and the implementation scale is different for each control.",
    "document_state": "Good content does not make a document valid; the catalog separates adopted, up to date and complete (golden 1, 2).",
    "document_relation": "The system has to know which document is authoritative and notice what is missing (golden 3, 6).",
    "implementation_evidence": "Implementation must not be inferred from paper, and without relevant evidence there is no level (golden 4, 5).",
}

# Combinations that cannot exist are removed before generation (Step 2):
# - irrelevant documents only: document_state and document_relation do not apply
# - evidence only, no paper: document_state does not apply
