# Week 2 submission

## Where each deliverable is

| Deliverable | Where |
| --- | --- |
| Video walkthrough (under five minutes) | (link added after recording) |
| Axes, with a reason each | `02_Open_Weights/challenge/axes.py`, the same table in `use_case/data/DATASHEET.md` |
| Generation, dedupe and validation code | `02_Open_Weights/challenge/generate.py` |
| Four counts and the settings | `use_case/data/DATASHEET.md`, "What this data is" |
| Dedupe threshold | `use_case/decisions.md`, Week 2 |
| Leak check and what I removed after reading | `use_case/data/DATASHEET.md`, "Leakage check, outward" |
| What it cannot validate, what it must never be compared against | `use_case/data/DATASHEET.md` |
| Goldens provenance | `use_case/data/DATASHEET.md`, "Leakage check, inward" |
| Model and endpoint | `use_case/decisions.md`, Week 2 |
| Review with the project lead | `use_case/stakeholders.md`, `use_case/decisions.md` and Step 6 below |
| What I would swap to run this at work | `## Bring it to work` in `02_Open_Weights/challenge/README.md` |
| Blocked model download | `use_case/ecosystem.md`, Week 2 |
| The dataset (548 rows) | `use_case/data/synthetic_v1.jsonl`, gitignored, not in the repo |

## Step 6, review with the project lead

My notes from going through 20 rows and the datasheet together.

- Never happens: nothing impossible, but six levels are not backed by the documents (examples 4, 5, 6, 8, 9 and 18 of the 20).
- Missing: scans, big packages, technical evidence like config exports and logs, evidence sent later.
- Worry if public: that the data looks validated when nobody checked the levels.
