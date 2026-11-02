# Evals

## `golden.jsonl`

Eight examples, written by hand: six in TC1 Step 7 and two in TC4, for gaps the
week showed. Not fifty, and not generated.

Each line is one object:

```json
{"input": "...", "output": "...", "why": "what makes this the right answer"}
```

The `why` field is the one that earns its keep. In Week 4 you calibrate an
LLM judge against these, and "why" is what you calibrate it on.

### Why you write these by hand

They are the fixed point of the whole cohort. A model-generated example encodes
what the model already does; a hand-written one encodes what *you* would accept,
which is the only thing worth measuring against.

| Week | What uses this file |
| --- | --- |
| 2 | Seeds for synthetic data generation — your variation axes come from these. |
| 4 | The eval harness scores against them, and the judge is calibrated on them. |
| 6 | Injection regressions get added alongside them. |
| 8 | **The bar.** A fine-tuned open model has to pass the same harness the closed one did. |

Get them wrong now and every number for the next nine weeks is measuring the
wrong thing.

### Writing good ones

- Use **real inputs** from your work, with names and identifiers removed.
- Write the output you would **actually accept**, not an idealized one.
- Include at least one **edge case** and one where the right answer is *"I don't
  know"* or *"escalate this"*. A system that never declines is not calibrated.
- Keep them short enough to read in full during review.

## `retrieval.jsonl`

Ten real questions from your use case, written in TC3, each labelled with the
record(s) in `use_case/data/synthetic_v1.jsonl` that should answer it — plus
the five your first real user typed. One object per line:

```json
{"question": "...", "gold": ["<record id>", "<record id>"], "kind": "lookup | multi-hop | decline"}
```

`gold` lists **every** record needed, because the measure is complete answers,
not "something relevant came back". At least one question is a `decline` — one
your data cannot answer — so you find out whether the endpoint knows when its
top *k* is the wrong answer.

| Week | What uses this file |
| --- | --- |
| 3 | Scores three or more retrieval techniques against each other. The decision in `decisions.md` cites the numbers. |
| 4 | The retrieval half of the eval harness — recall and completeness, tracked per change. |
| 6 | Injection regressions arrive through retrieved content; these are the questions they must not break. |

## The Week 4 harness

Technical Challenge 4 adds the files that turn this folder into a harness
every later week runs. `python use_case/evals/run.py` is the whole interface.

| File | What it is | Written in |
| --- | --- | --- |
| `failures.md` | What goes wrong, ranked, with counts — from fifty real traces. Every scorer traces back to a line here | TC4 Step 1 |
| `human_scores.jsonl` | Fifty outputs I scored by hand: `{"input", "actual", "pass", "why"}`. The judge's agreement is measured against these | TC4 Step 1 |
| `harness.py` | Your scorers, `run_eval`, `report`, `bootstrap_ci`, the judge rubric | TC4 Steps 2–3 |
| `synthetic.jsonl` | Generated failures, each with the original, the corruption and its failure mode | TC4 Step 4 |
| `scenarios.py` | Not written: the endpoint answers one request and holds no conversation (`decisions.md`, Week 4) | TC4 Step 5 |
| `run.py` | Points the harness at your endpoint and prints the report | TC4 Step 6 |
| `baseline.json` | **The run itself**, saved with `helpers.harness.save`. Commit it | TC4 Step 6 |


### Results, 2 Nov

**Scorers, echo and oracle (Step 2).** Each scorer is averaged over the cases it is about. The app row replays the 50 answers I read in Step 1.

| System | documents_found (45) | level_matches (6) | declines_when_no_evidence (5) | only_case_documents (50) |
| --- | ---: | ---: | ---: | ---: |
| echo | 0.00 | 0.17 | 1.00 | 1.00 |
| oracle | 1.00 | 1.00 | 1.00 | 1.00 |
| app, 1 Nov | 0.90 | 1.00 | 0.40 | 0.83 |

Echo gives no level and no sources, so it passes the two scorers that only punish a wrong level or a wrong source. Read them together with documents_found, where echo scores 0.00. On level_matches echo gets 0.17 because golden-5 expects no level.

**Judge (Step 3).** `judge_level_basis`, on Opus 5.5, asks one question for failures.md #2: is each level backed by the key condition that separates it from the level below.

- Separation on the four settled goldens (4 and 6 are unresolved, so not known-good): accepted answers 1.00, echo 0.00, a wrong answer 0.00.
- Agreement with my 50 verdicts: 0.62, chance floor 0.51. The first rubric scored 0.50 against a floor of 0.50.
- Used as a separate column, not the headline.

**Generated failures (Step 4).** Natural: I would not accept 24 of the 50 traces (search miss 9, level without basis 8, unrelated documents 7). Generated: 170 rows in `synthetic.jsonl`, from the 26 answers I accepted (161 distinct).

| Failure mode | Difficulty | Generated | documents_found | level_matches | declines_when_no_evidence | only_case_documents | judge_level_basis |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| drop_source | easy | 24 | 1.00 | 0.00 | 0.00 | 0.08 | not run |
| drop_source | hard | 24 | 1.00 | 0.00 | 0.00 | 0.08 | not run |
| level_up | easy | 24 | 0.00 | 0.17 | 0.00 | 0.00 | 0.96 |
| level_up | hard | 24 | 0.00 | 0.17 | 0.00 | 0.00 | 0.96 |
| unrelated_source | easy | 24 | 0.00 | 0.00 | 0.00 | 1.00 | not run |
| unrelated_source | hard | 24 | 0.00 | 0.00 | 0.00 | 1.00 | not run |
| false_decline | easy | 24 | 1.00 | 0.17 | 0.00 | 0.00 | 0.00 |
| skip_decline | easy | 2 | 0.00 | 0.50 | 1.00 | 1.00 | 1.00 |

Easy and hard score the same, because these failures change the sources or the level number, which the scorers check exactly. For answers at level 4 the easy and hard level_up rows are the same answer, so this set does not test the judge on subtle cases. The judge does not read the sources, so it runs only on the level and decline modes.

**Baseline (Step 6).** `run.py --save` on 52 cases (the 50 plus goldens 7 and 8), 2 Nov:

| Scorer | Cases | Mean |
| --- | ---: | ---: |
| documents_found | 47 | 0.85 |
| level_matches | 8 | 1.00 |
| declines_when_no_evidence | 5 | 0.40 |
| only_case_documents | 52 | 0.77 |
| judge_level_basis | 52 | 0.85 |

Headline: documents_found 0.85, 95% CI [0.77, 0.92] on 47 cases. Two answers crashed the app (invalid JSON from the model) and count as 0.

```
PASS  week4-baseline → week4-baseline  [declines_when_no_evidence +0.000  documents_found +0.000  judge_level_basis +0.000  level_matches +0.000  only_case_documents +0.000]
```

| Week | What uses these files |
| --- | --- |
| 5 | The demo leads with `baseline.json`'s headline number, and the critique goes after it. |
| 6 | Every guardrail is re-run through `run.py`; the winning attack becomes a permanent case and a new line in `failures.md`. |
| 7 | Three memory tests join `scenarios.py`. |
| 8 | **The bar.** `harness.compare(harness.load("baseline.json"), finetuned)` is the pass/fail — and it refuses if the case set changed. |
| 9 | The harness gates the deploy. |
| 10 | A sampled version runs on live traffic. |
