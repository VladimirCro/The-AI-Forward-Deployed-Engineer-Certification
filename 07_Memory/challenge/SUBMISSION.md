# Week 7 submission

I gave the assessment tool a memory of what it did. Each assessment and each of the consultant's decisions is now kept in one SQLite file, so a past answer can be explained, and when she changes a level the new decision replaces the old one and the old one stays in the history. Four tests in the harness check it: staleness, cost, truthfulness and leakage. Each of them failed when I broke what it checks.

Loom video: https://www.loom.com/share/1b339825f63244d8b90b81fc4c32facc

## Where each deliverable is

| Deliverable | Where |
| --- | --- |
| Video: the memory, the four tests and the run that checks them | Link above |
| The choice of kind, and the kinds I rejected | [`use_case/decisions.md`](https://github.com/VladimirCro/The-AI-Forward-Deployed-Engineer-Certification/blob/main/use_case/decisions.md), Week 7 |
| The memory | [`memory.py`](https://github.com/VladimirCro/The-AI-Forward-Deployed-Engineer-Certification/blob/main/01_Product_Engineering/challenge/memory.py); written by [`assess.py`](https://github.com/VladimirCro/The-AI-Forward-Deployed-Engineer-Certification/blob/main/01_Product_Engineering/challenge/assess.py) and by `record_consultant_decision` in [`app.py`](https://github.com/VladimirCro/The-AI-Forward-Deployed-Engineer-Certification/blob/main/01_Product_Engineering/challenge/app.py) |
| Explaining a past assessment | `explain()` in `assess.py`, endpoint `explain_assessment` in `app.py` |
| The four memory tests | Week 7 part of [`use_case/evals/harness.py`](https://github.com/VladimirCro/The-AI-Forward-Deployed-Engineer-Certification/blob/main/use_case/evals/harness.py), run by `memory_report()` in [`use_case/evals/run.py`](https://github.com/VladimirCro/The-AI-Forward-Deployed-Engineer-Certification/blob/main/use_case/evals/run.py) |
| Before and after on the harness numbers | Below: baseline from 13 Nov (`use_case/evals/baseline.json`), run on 23 Nov |
| It still runs in Docker | Run it below |

## The choice: episodic

Sooner or later someone asks why the tool proposed a level, for example the consultant a few weeks later or an auditor. Until now nothing was kept to answer that. Semantic memory did not fit, because the consultant has no stable facts the tool keeps asking for, and a fact without a document behind it should never reach an assessment. Procedural memory did not fit either: in Week 5 a search planned up front found fewer documents (0.79 against 0.93), and learned search steps could do the same. The full reasoning is in `decisions.md`.

An episode holds what the code saw: the documents the search returned, the label and reason for each, the documents kept as relevant, the quotes the check dropped because they were not in the document word for word, and the answer. Her decisions go into the same file.

## Staleness: supersede on write

One live entry per client, control, kind and dimension. When she changes a level, the earlier decision is marked replaced and kept with its time and reason, so the history is there for an audit, but only one decision counts. A unique index on live entries means the database itself refuses a second one.

For assessments the subject is the client and the control, and the episode carries a hash of what the answer depends on: the text of all the client's documents, the model, and which search ran. If the hash is the same, the stored answer comes back without a model call. If a document, the model or the search changed, the tool assesses again.

## The tests

They run on an empty memory file of their own, apart from the 52 cases, so the fingerprint of the main run does not change and the comparison with the baseline still holds. If one fails, `run.py` stops.

| Test | What it does | Result |
| --- | --- | --- |
| Staleness | She accepts 3, then changes it to 2 with a reason, through the same function the frontend calls. The live decision must be 2, and the history 3 then 2. Then one of the client's documents changes (in a copy of the folder): the next assessment must be a new one, and the old one only in the history. | passed |
| Cost saving | One real case assessed twice, counting every chat model call (the embedding calls are not counted, and the second time there are none of those either). The second must make none and give the same answer. | passed: 6 model calls the first time, 0 the second |
| Truthfulness | The tool explains that assessment. Every document and quote it names must be in the episode, and it must name at least one when the assessment used documents. | passed: 8 documents and 3 quotes, all in the log |
| Leakage | Another client asks about the same control and must see none of the first client's decisions or assessments. | passed |

The numbers are from the full run on 23 Nov. The search does not take the same path every time, so another run gave 5 calls the first time, still 0 the second.

There are no user accounts in the app, but the clients' data must never mix, so I wrote the leakage test anyway. The saving comes from reusing a stored answer when nothing changed; the tool does not search any better.

## Do the tests catch a broken memory

I broke each part on purpose and ran the test that guards it:

| What I broke | Test that failed |
| --- | --- |
| A new decision no longer marks the old one replaced | Staleness: the database refused the second live entry |
| The memory ignores the client | Leakage |
| The explanation names a document that is not in the log | Truthfulness |
| The explanation names nothing | Truthfulness |
| The stored answer is never read | Cost saving: 6 model calls the second time too |
| The hash ignores the documents | Staleness: after the changed document the old answer came back |

## Before and after

The same 52 cases, the same judge, against the baseline from 13 Nov (the Week 4 baseline no longer compares since the harness changed in Week 6, see `decisions.md`).

| Scorer | Cases | Before | After |
| --- | ---: | ---: | ---: |
| documents_found (headline) | 47 | 0.88 | 0.92 |
| level_matches | 8 | 1.00 | 1.00 |
| declines_when_no_evidence | 5 | 0.40 | 0.40 |
| only_case_documents | 52 | 0.82 | 0.81 |
| judge_level_basis | 52 | 0.88 | 0.87 |

`run.py` says PASS: every change is inside the 0.08 tolerance, and they go both ways, which is what three runs of the same app also did. Seconds per case: median 58, against 56 in the baseline.

The memory did not make the answers worse, but this run cannot show the case where it could. Every case is a different client and control, so the memory only wrote: after the run it held 52 assessments, all live, none reused. The week warns about a wrong entry coming back as if it were right. For me that would be an old answer coming back after something outside the hash changed, such as the prompt.

## What is still weak

- When a client sends one new document, the hash changes and the whole assessment runs again. The better version keeps the documents from the last episode and reads only the new one.
- The hash has no version of the prompt, the catalog or a `SKILL.md`. After changing one of them, the memory file has to start empty. The same goes for a second `run.py` against the same container, and for the Week 5 scripts on the host: without a new memory file they score the stored answers.
- A decline is stored like any answer, also one where the search ran out of turns, and comes back until a document changes. There is no way yet to ask for a new assessment.
- There is one live assessment per client and control, whichever search made it, so the tool and the skill replace each other.
- The episode keeps what the search returned, not each search it made.
- In the container the file is in `/tmp` and goes away with it, decisions included. A real deployment needs a volume or a database.
- The truthfulness test checks the ids an explanation names, not what it says about them.

## Run it

```bash
cd 01_Product_Engineering/challenge
uv run --no-sync --env-file ../../.env python ../../use_case/evals/run.py memory
```

Only the memory tests, in this process, on an empty file: one real assessment, about a minute and a half. A plain `run.py` with the app running runs them after the 52 cases and the guardrail check.

Docker, from the repo root, the same as in Week 6:

```bash
docker build --build-arg HTTPS_PROXY="$HTTPS_PROXY" -t enterprise-fde-challenge 01_Product_Engineering/challenge
docker run --rm -p 7860:7860 --env-file .env \
  -v "$PWD/use_case/data/clients:/data/clients:ro" -e CLIENTS_DIR=/data/clients \
  enterprise-fde-challenge
```

On 23 Nov `run.py` ran against this container with the memory in it. After the run its memory held 52 assessments.
