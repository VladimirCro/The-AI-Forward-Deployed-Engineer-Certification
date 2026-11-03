# Week 4 submission

An eval harness for the Week 3 endpoint, which assesses one control for one fictional client. It scores the endpoint on 52 cases, compares every run with a saved baseline, and runs with one command.

Loom video: https://www.loom.com/share/aaf6f0425bde4d69bf2602971abfcfba

## Where each deliverable is

| Deliverable | Where |
| --- | --- |
| Video, the five-minute demo | Link above |
| Failure taxonomy | `use_case/evals/failures.md` |
| Hand scores (50) | `use_case/evals/human_scores.jsonl` |
| Scorers, judge rubric, interval | `use_case/evals/harness.py` |
| Scorer table with echo and oracle, calibration, detection table, baseline | "Results, 2 Nov" in `use_case/evals/README.md` |
| Generated failures | `use_case/evals/synthetic.jsonl` |
| Goldens (8, goldens 7 and 8 added this week) | `use_case/evals/golden.jsonl` |
| The fifty traces and their clients | `use_case/evals/collect_traces.py`, `use_case/evals/build_trace_clients.py` (the traces and documents are gitignored) |
| `run.py` and the saved run | `use_case/evals/run.py`, `use_case/evals/baseline.json` |
| Trajectory table | Not built, see Step 5 below |
| Decision row | `use_case/decisions.md`, Week 4, second row |
| Step 7, demo review with a real user | `use_case/stakeholders.md`, Week 4; what it changed in `use_case/decisions.md`, Week 4, third row |
| Swap lines | `## Bring it to work` in `04_Evals/challenge/README.md` |
| Gateway and model notes | `use_case/ecosystem.md`, Week 4 |

## Taxonomy and hand scores

I read fifty traces from the Week 3 endpoint: the 10 retrieval cases, the 6 goldens and 34 rows from the Week 2 data, each turned into a fictional client of about 150 documents. I would not accept 24 of the 50 answers and would accept 26.

| # | Main reason | Count |
| --- | --- | ---: |
| 1 | The search misses an important document of the case | 9 |
| 2 | The level has no basis in the evidence | 8 |
| 3 | It builds the answer on documents that are not evidence for this control | 7 |

In 16 of the 24 the problem is which documents reach the assessment. Each failure has its own sentence in `failures.md`.

## Scorers, echo and oracle

Each scorer is averaged over the cases it is about. The app row replays the 50 answers I read.

| System | documents_found (45) | level_matches (6) | declines_when_no_evidence (5) | only_case_documents (50) |
| --- | ---: | ---: | ---: | ---: |
| echo | 0.00 | 0.17 | 1.00 | 1.00 |
| oracle | 1.00 | 1.00 | 1.00 | 1.00 |
| app, 1 Nov | 0.90 | 1.00 | 0.40 | 0.83 |

## Calibration and whether I used the judge

The judge, `judge_level_basis` on Opus 5.5, checks failure #2: is each level backed by the key condition that separates it from the level below.

- Separation on the four settled goldens: oracle (the golden answers) 1.00, echo 0.00, a wrong answer 0.00.
- Agreement with my 50 verdicts: 0.62, chance floor 0.51. The first rubric scored 0.50 against a floor of 0.50.

Agreement is weak (the course's own example calls 0.60 not used), so the judge sets no number I report. It stays in `run.py` as an extra column, to see whether it improves once the decision rules are written.

## Detection

Natural: I would not accept 24 of the 50 traces (search miss 9, level without basis 8, unrelated documents 7). Generated: 170 rows in `synthetic.jsonl` from the 26 answers I accepted. The table per failure mode and difficulty is in "Results, 2 Nov" in `use_case/evals/README.md`.

## Step 5, trajectories

Skipped. The endpoint answers one request and holds no conversation, so there is no trajectory table and no `pass^k`. This is written in the decision row.

## Headline and the saved run

`run.py --save` on 52 cases (the 50 plus goldens 7 and 8), 2 Nov:

Headline: documents_found 0.85, 95% CI [0.77, 0.92] on 47 cases. Two answers crashed the app on invalid JSON from the model and count as 0.

`baseline.json` stores means over all 52 cases; `run.py` reports each scorer over the cases it is about, as in "Results, 2 Nov" in `use_case/evals/README.md`.

```
PASS  week4-baseline → week4-baseline  [declines_when_no_evidence +0.000  documents_found +0.000  judge_level_basis +0.000  level_matches +0.000  only_case_documents +0.000]
```

## Decision row

`use_case/decisions.md`, Week 4, second row: the headline, why not the judge, what it does not cover and what would change my mind.

## Step 7, demo review

Done in writing on 2 November with the GRC consultant: the five-minute demo (problem, numbers, one failure, next steps) and three questions. There was no time for a live session before the deadline, so I sent her the demo and eight cases and she answered in writing. A two-hour session with her is booked for Thursday, 5 November.

- **What would you do differently on Monday?** She would run a limited pilot with mandatory consultant review and measure the time really saved, including review and corrections.
- **What would convince you the number is wrong?** An independent review of all 50 answers against rules agreed in advance that gives different results, with the exact version of every answer kept.
- **What did you expect to see?** The assessment date, the original document one click away, and a view of which condition of the level is confirmed and which is not.

Her full answers are in `use_case/stakeholders.md` (Week 4), and what they changed in `use_case/decisions.md` (Week 4, third row).

## Swap lines

Under `## Bring it to work` in `04_Evals/challenge/README.md`. One `run.py` makes 62 judge calls and 52 app calls and took 52 minutes, measured on 2 Nov.

## Run it

The app must be running (the `tc3-app` container on port 7860, see the Week 3 submission), and `.env` needs `LLM_THINKING=between_tools`. From a clean checkout it does not run: 34 of the cases and all client documents come from `use_case/data/synthetic_v1.jsonl` and `synthetic_v2.jsonl`, which are gitignored and were generated by a model in Week 2, so they cannot be rebuilt the same. With those files in place, `build_clients.py` and `build_trace_clients.py` build the clients. `run.py` runs from the app's environment. Run `uv sync` once in `01_Product_Engineering/challenge`; after that `--no-sync` keeps the environment as it is.

```bash
cd 01_Product_Engineering/challenge
uv run --no-sync --env-file ../../.env python ../../use_case/evals/run.py
```

It prints the report and compares the run with `baseline.json`. Add `--save` only to re-baseline on purpose.

It still runs in Docker: the 52-case baseline on 2 Nov ran against the app in the `tc3-app` container, built with the Week 3 commands.
