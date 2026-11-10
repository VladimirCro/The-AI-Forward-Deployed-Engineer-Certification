# Week 5 submission

A second way for the Week 3 endpoint, which assesses one control for one fictional client. I built the search as a skill, measured it against the tool loop on the same two requests and on the Week 3 cases, and kept the tool loop. The architecture row in `use_case/decisions.md` says why and what would make me switch.

Loom video: https://www.loom.com/share/b6583334a0bf4c1ea22e2f5496e98805

## Where each deliverable is

| Deliverable | Where |
| --- | --- |
| Video, the refined five-minute demo | Link above |
| What changed after critique | The paragraph below, and the top of [`## Week 5: the second way, measured`](https://github.com/VladimirCro/The-AI-Forward-Deployed-Engineer-Certification/blob/main/05_Agent_Architecture/challenge/README.md#week-5-the-second-way-measured) in `05_Agent_Architecture/challenge/README.md` |
| The room's questions, with their marks | [`use_case/decisions.md`](https://github.com/VladimirCro/The-AI-Forward-Deployed-Engineer-Certification/blob/main/use_case/decisions.md), "Week 5 — what the room asked" |
| The second way, and why | "The second way, and why" below |
| The second implementation | [`skill.py`](https://github.com/VladimirCro/The-AI-Forward-Deployed-Engineer-Certification/blob/main/01_Product_Engineering/challenge/skill.py), [`skills/`](https://github.com/VladimirCro/The-AI-Forward-Deployed-Engineer-Certification/tree/main/01_Product_Engineering/challenge/skills) (a `SKILL.md` per control and `run.py`), `assess_control_with_skill` in [`app.py`](https://github.com/VladimirCro/The-AI-Forward-Deployed-Engineer-Certification/blob/main/01_Product_Engineering/challenge/app.py) |
| The dispatcher's failure messages | `dispatch` in `skill.py`, and the README section |
| Demo-scale measurement and the parallel-tool-call count | README section; [`measure.py`](https://github.com/VladimirCro/The-AI-Forward-Deployed-Engineer-Certification/blob/main/05_Agent_Architecture/challenge/measure.py) |
| Real-size row | README section |
| Whether the skill finds the documents | README section; [`accuracy.py`](https://github.com/VladimirCro/The-AI-Forward-Deployed-Engineer-Certification/blob/main/05_Agent_Architecture/challenge/accuracy.py) |
| Architecture row | `use_case/decisions.md`, Week 5, first row |
| Step 7, the refined demo shown to the consultant | [`use_case/stakeholders.md`](https://github.com/VladimirCro/The-AI-Forward-Deployed-Engineer-Certification/blob/main/use_case/stakeholders.md), Week 5; what it changed in `use_case/decisions.md`, Week 5, second row |
| Swap lines | [`## Bring it to work`](https://github.com/VladimirCro/The-AI-Forward-Deployed-Engineer-Certification/blob/main/05_Agent_Architecture/challenge/README.md#bring-it-to-work) in `05_Agent_Architecture/challenge/README.md` |
| It still runs in Docker | Last paragraph of the README section; commands in "Run it" below |
| Repo link on Maven | Posted after this is pushed |
| Comments on two other submissions | After the deadline |

## What changed after critique

The room's questions (decisions.md, Week 5) gave me two fixes. The headline now always sits next to what I would accept: documents_found 0.85, and I would accept 26 of 50 answers. The screen now says each level is the tool's proposal, with an accept or change step that needs a reason and is recorded. The open question, what I rejected, I answered by building a second way and measuring it (below, and the architecture row). The consultant's review of the refined demo changed one more thing: her worst case is a level that is too high with real quotes that don't prove the condition. Every accept or change is now recorded with its reason, and counting the proposals above her decision is the next step.

## The room's questions

In `use_case/decisions.md`, under "Week 5 — what the room asked": two fair, one open, the rest answered. I was not at Session 9, so these are the rubric's questions plus the replies to my TC4 post on Maven.

- **Fair:** "Show 'would accept' next to 0.85." The Week 5 texts and the demo show "would accept: 26 of 50" next to 0.85.
- **Fair:** "The app doesn't show that the consultant decides." The answer is labelled as a proposal, with a step where she accepts or changes the level.
- **Open:** "What did you consider and reject?" Answered by the skill below and the architecture row.

## The second way, and why

**Second way: a skill.** Question 4 picked it: what each control asks for and what counts as evidence is knowledge the consultant owns, and it will change more often than the code. Questions 1 and 2 were no: the capability is not an existing API at work, and only my own frontend calls it. Question 3 was yes (in Week 3 about 4.7 searches of about 2 KB per request; 4 to 9 in this week's runs), but Code Mode needs a sandbox I don't have, so it stays a paragraph.

**Closest alternative I did not pick: a subagent.** The search does read a lot to return a little (in Week 3 about 9,300 characters for 3 or 4 documents), but it already runs as one fixed step with its own prompt, so a second model in front of it adds a call without new information.

## The dispatcher

Asked for a tool that does not exist, the model gets back `Unknown tool: lookup_team. Available tools: search_documents`. Arguments that do not parse come back as `Arguments were not a JSON object with queries: ...`, and the model tries once more (`skill.py`, `dispatch`).

## Both ways at demo scale

The same two requests, measured 8 Nov with `measure.py`:

| Request | Way | Model calls | Capability calls | Seconds | Tokens | Embedding tokens |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| klijent-01 POL-001 | tool | 6 | 7 | 58.9 | 27,836 | 12,606 |
| klijent-01 POL-001 | skill | 3 | 7 | 66.7 | 8,746 | not visible |
| klijent-05 ORG-001 | tool | 5 | 4 | 59.4 | 17,075 | 12,353 |
| klijent-05 ORG-001 | skill | 3 | 10 | 84.8 | 8,960 | not visible |

Parallel tool calls: yes. The tool loop asked for 3 searches in its first turn on both requests, so its 4 to 7 searches took 3 to 4 model turns. The skill plans every search in one call.

The skill's searches run in a subprocess, so the counter in my process could not see them: `run.py` writes one line per search and I counted those. The embedding tokens for its queries are not counted at all.

No request in my use case needs a single search: every assessment ran at least four, so both requests are the "several calls" kind.

## Real response size

Measured 8 and 9 Nov. The searches already return whole pages of my synthetic documents, so demo size is the real size of this data. Real client documents are longer.

| Way | Bytes per search | Searches per request | Model tokens per request |
| --- | ---: | ---: | ---: |
| tool loop | 1,824 to 2,113 | 4 to 9 | 17,075 to 39,437 |
| skill, planned up front | 927 to 1,009 | 7 to 10 | 7,846 to 9,049 |
| skill in a loop, up to 8 results per search | 1,914 to 1,989 | 4 to 8 | 13,724 to 31,994 |

At ten times the volume each way costs ten times its tokens: for the tool loop about 170,000 to 395,000 model tokens for ten requests, plus about 125,000 embedding tokens, because the Week 3 endpoint embeds all 150 pages on every request.

Whether they find the documents (`accuracy.py`, 8 Week 3 cases with labelled documents): tool loop 0.93 on average over six runs, the skill planned up front 0.79 over six, the skill in a loop with up to 8 results per search 0.92 over three. So the token saving came from reading fewer results, not from the skill. The full table is in the README section.

## Architecture row

`use_case/decisions.md`, Week 5, first row.

- **Decision:** a tool. The search stays a tool loop in my own process. What each control asks for will live in a markdown file per control that the consultant can edit.
- **Closest reject:** the skill, which I built in three versions. Planned up front it read 2 to 4 times fewer tokens but found fewer documents (0.79 against 0.93). In a loop with as many results per search as the tool it found as many (0.92) and cost about as many tokens, while every search ran in a subprocess my counter could not see.
- **Why:** questions 1 and 2 no; question 3 yes, but Code Mode needs a sandbox; question 4 yes, but the control is always known in advance, so the model never has to choose a skill and progressive disclosure buys nothing; question 5 is already handled by the search step. The consultant also expects the tool to search again when a key condition is unclear, which a loop does.
- **Switch condition:** a real skill if one request has to work across many controls; Code Mode, once there is a sandbox, if real documents make one search return more than about 10 KB; MCP if a second client needs the assessment.

## Step 7, demo review

Done in writing on 9 November with the GRC consultant, because she prefers to review written material: what changed after critique, one answer with the accept or change step, the klijent-10 failure, the numbers and the architecture I measured, then the three questions.

- **What would you do differently on Monday?** Run it on one of the three controls next to her own review and measure how much time it really saves once checking is counted.
- **What did I say that you did not believe?** She does not yet trust the proposed levels: it declines correctly in only 2 of 5 no-evidence cases, and it still has to show it recognises what a document proves.
- **What is the worst thing this could do?** A level that is too high, with a convincing rationale and real quotes that do not prove the condition, which she misses and accepts.

What changed (`use_case/decisions.md`, Week 5, second row): a proposed level higher than her decision will be counted on its own, next to the headline, and when the evidence a level needs is missing the tool will give no level with a reason and the next step. Decided, not built yet: today every accept or change is recorded with its reason, and nothing counts them yet. Her full answers are in `use_case/stakeholders.md`, Week 5.

## Swap lines

Under `## Bring it to work` in `05_Agent_Architecture/challenge/README.md`. The capability is the search over one client's documents, which the assessment runs as a tool loop.

- **Data:** about 50 to 200 files per client; today 4 to 9 searches per request, 1.8 to 2.1 KB per search, 17,075 to 39,437 model tokens per request (measured, 8 and 9 Nov).
- **Model or endpoint:** the same internal AI gateway; the documents arrive as files, not behind an existing API; the app team holds the gateway key.
- **Approval:** client consent, a deployment review, and the security and privacy reviews. No sandbox, because I kept the tool loop.

## Run it

The clients must be built by `build_clients.py`, from the Week 2 data that is gitignored (see the Week 4 submission), and `.env` needs `LLM_THINKING=between_tools`. Run `uv sync` once in `01_Product_Engineering/challenge`.

```bash
cd 01_Product_Engineering/challenge
uv run --no-sync --env-file ../../.env python ../../05_Agent_Architecture/challenge/measure.py klijent-01 POL-001
uv run --no-sync --env-file ../../.env python ../../05_Agent_Architecture/challenge/accuracy.py
```

`measure.py` prints the four columns for one request, both ways. `accuracy.py` runs the ten Week 3 cases each way; `accuracy.py "skill loop"` runs only one way.

Docker, from the repo root, with the Week 3 commands:

```bash
docker build -t enterprise-fde-challenge 01_Product_Engineering/challenge
docker run --rm -p 7860:7860 --env-file .env \
  -v "$PWD/use_case/data/clients:/data/clients:ro" -e CLIENTS_DIR=/data/clients \
  enterprise-fde-challenge
```

On 9 Nov in the container both assessment endpoints answered klijent-03 POL-001 with documentation 3 and implementation 4 and all three labelled documents (56 s for the tool loop, 150 s for the skill), and `record_consultant_decision` wrote its record.
