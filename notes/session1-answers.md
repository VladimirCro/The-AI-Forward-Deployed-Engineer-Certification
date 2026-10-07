# Session 1 — my answers

Answers to the questions in `01_Product_Engineering/sessions/S1_Enterprise_Dev_Environment.py`.
Kept in a separate file so the notebook stays identical to upstream.

## Question #1 — what the issuer column predicts that the status column cannot

Status only tells me the TLS handshake worked here, with this tool. The issuer
tells me whether the certificate is public or private (signed by my company),
so it predicts whether the application will work in other environments, like a
container, a server or Python's own trust store, which may not trust the
company CA.

## Question #2 — how `make check` can pass on a notebook that raises on cell three

`make check` compares the original (`.py`) and the copy (`.ipynb`) byte by byte,
but it never runs the code, so if the original has a bug, the copy has the same
bug and the check still passes. A byte-comparison gate only promises that the
two versions are consistent, not that the notebook is correct.
