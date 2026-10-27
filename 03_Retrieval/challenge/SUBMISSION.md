# Week 3 submission

## Where each deliverable is

| Deliverable | Where |
| --- | --- |
| Video walkthrough (under five minutes) | TODO: Loom link |
| Ten labelled questions | `use_case/evals/retrieval.jsonl` |
| Top-k floor | `## Retrieval notes` in `03_Retrieval/challenge/README.md` |
| Schema: implemented, not redesigned | `use_case/decisions.md`, Week 3, first row (`sources` added to `Response`; `Request` and `solve()` unchanged) |
| Retrieval code (BM25, direct corpus interaction, dense, hybrid) | `01_Product_Engineering/challenge/retrieval.py` |
| The fictional clients the retrieval runs on | `01_Product_Engineering/challenge/build_clients.py` (the documents are gitignored) |
| Results table with its settings, the range over seven runs, the embedding token count | `03_Retrieval/challenge/results.md`, made by `01_Product_Engineering/challenge/measure.py` |
| The endpoint and its docstring | `assess_control_for_client` in `01_Product_Engineering/challenge/app.py`; the steps in `01_Product_Engineering/challenge/assess.py` |
| The endpoint on the ten questions | `03_Retrieval/challenge/endpoint_results.md`, made by `01_Product_Engineering/challenge/answer_cases.py` |
| What it does on the decline question | `## Retrieval notes` in `03_Retrieval/challenge/README.md` |
| Retrieval decision and the four non-text answers | `use_case/decisions.md`, Week 3 |
| Model for the whole app | `use_case/decisions.md`, Week 3 |
| Runs in Docker | `01_Product_Engineering/challenge/Dockerfile`; the clients are mounted, not copied in |
| Demo to a real user | Scheduled, see Step 6 below |
| What I would swap to run this at work | `## Bring it to work` in `03_Retrieval/challenge/README.md` |
| Gateway and model notes | `use_case/ecosystem.md`, Week 3 |

## What a question is here

The tool has no questions typed by people: a consultant asks it to assess one control for one client. So one case is a fictional client with about 150 documents and one control, and the labelled answer is every document the assessment needs. 8 of the 10 need more than one document, and 2 have no evidence at all.

## Step 6, demo to a real user

Scheduled with a consultant for Monday, 2 November 2026, after the deadline. The consultant sends five situations from client work beforehand; I build a fictional client for each, run the endpoint live, and ask the three questions from the challenge. Their answers, the five new labelled cases and what they changed go into `use_case/stakeholders.md`, `use_case/evals/retrieval.jsonl` and `use_case/decisions.md` after the session.
