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
| Results table with its settings, the range over three runs, every run of the day, the embedding token count | `03_Retrieval/challenge/results.md`, made by `01_Product_Engineering/challenge/measure.py` |
| The endpoint and its docstring | `assess_control_for_client` in `01_Product_Engineering/challenge/app.py`; the steps in `01_Product_Engineering/challenge/assess.py` |
| The endpoint on the ten questions, three runs | `03_Retrieval/challenge/endpoint_results.md`, made by `01_Product_Engineering/challenge/answer_cases.py` |
| What it does on the decline question | `## Retrieval notes` in `03_Retrieval/challenge/README.md` |
| Retrieval decision and the four non-text answers | `use_case/decisions.md`, Week 3 |
| Model for the whole app | `use_case/decisions.md`, Week 3 |
| Runs in Docker | `01_Product_Engineering/challenge/Dockerfile`; the commands are under "Run it" below |
| Demo to a real user | Scheduled, see Step 6 below |
| What I would swap to run this at work | `## Bring it to work` in `03_Retrieval/challenge/README.md` |
| Gateway and model notes | `use_case/ecosystem.md`, Week 3 |

## What a question is here

The tool has no questions typed by people: a consultant asks it to assess one control for one client. So one case is a fictional client with about 150 documents and one control, and the labelled answer is every document the assessment needs. 8 of the 10 need more than one document, and 2 have no evidence at all.

I chose the ten from the Week 2 data, one for each hard situation in its recipes, and checked every label by reading the documents. The consultant's own situations are added after the demo on 2 November.

| Case | Control | What makes it hard |
| --- | --- | --- |
| klijent-01 | POL-001 | The documents contradict each other and the policy itself is missing: the board claims full implementation, an internal audit says 78%. |
| klijent-02 | POL-001 | The policy is adopted, then a later board decision suspends part of it; read receipts exist for only 34 of 127 people. |
| klijent-03 | POL-001 | The adoption decision points to an annex with the policy text, and the annex was not handed over. |
| klijent-04 | POL-001 | Decline: only an incident report and a list of security tools, nothing about a policy. |
| klijent-05 | ORG-001 | The documents agree, but each covers a different part of the scale. |
| klijent-06 | ORG-001 | Two versions of the rulebook, one key role left empty, 16 of 18 role holders confirmed. |
| klijent-07 | ORG-001 | An email says four people were told and signed; the decision says two of three roles are still empty. |
| klijent-08 | EDU-001 | The training plan has to be compared with what the policy requires and who was trained (187 of 195). |
| klijent-09 | EDU-001 | Informal workshops with no attendance list, and a policy that is only on the intranet. |
| klijent-10 | EDU-001 | Decline: only a server purchase plan. |

## Run it

From the repo root, after building the clients once with `uv run python build_clients.py` in `01_Product_Engineering/challenge`. The `.env` needs `EMBED_MODEL` and `EMBED_API_BASE` next to the chat settings.

```bash
docker build -t enterprise-fde-challenge 01_Product_Engineering/challenge
docker run --rm -p 7860:7860 --env-file .env \
  -v "$PWD/use_case/data/clients:/data/clients:ro" -e CLIENTS_DIR=/data/clients \
  enterprise-fde-challenge
```

Then open http://localhost:7860, pick a client and a control, and press "Procijeni".

## Step 6, demo to a real user

Scheduled with a consultant for Monday, 2 November 2026, after the deadline. The consultant sends five situations from client work beforehand; I build a fictional client for each, run the endpoint live, and ask the three questions from the challenge. Their answers, the five new labelled cases and what they changed go into `use_case/stakeholders.md`, `use_case/evals/retrieval.jsonl` and `use_case/decisions.md` after the session.
