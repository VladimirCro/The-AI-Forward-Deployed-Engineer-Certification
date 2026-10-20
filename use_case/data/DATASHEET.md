# Datasheet

## What this data is

**Generated on:** 2026-10-20
**Generated from:** the Week 1 schema, the control catalog (the level criteria go into every prompt), the variation axes, and golden examples 3, 5 and 6 as format examples. No real records.
**Rows:** 548 (555 schema-valid, 1 removed after reading, 6 removed after the project lead's review)

| Count | |
| --- | --- |
| Generated | 562 |
| After dedupe | 562 |
| Schema-valid | 555 |
| Dead combinations | 0 (13 in the first run; those 13 were run a second time with the same settings and all produced rows) |

255 lines needed one extra closing brace removed before they could be read; 33 lines could not be read at all.

**Settings:** `openai/claude-haiku-4-5` through the internal gateway, temperature 0.7 (0.3 for the decline combinations), top_p 0.9, 2 rows per call, dedupe threshold 0.7, 288 combinations. Script: `02_Open_Weights/challenge/generate.py`.

## Variation axes

The same list as `02_Open_Weights/challenge/axes.py`. One request is one control plus the client's evidence documents.

| Axis | Values |
| --- | --- |
| control | POL-001 (top-level cybersecurity policy) · ORG-001 (roles, responsibilities and duties) · EDU-001 (staff awareness training) |
| document_state | adopted and in force · draft · not adopted or not signed · incomplete (a section or annex is missing) · badly or vaguely worded · outdated (adopted, but not reviewed for years) |
| document_relation | documents agree · documents contradict each other · several versions of the same document · a later event changes the situation · refers to a document that was not submitted |
| implementation_evidence | full evidence · partial evidence, near a level threshold · paper only, no evidence of implementation · evidence only, no paper · irrelevant documents only (decline: no level, ask for evidence) |

Combinations that cannot exist are removed before generation:
- *irrelevant documents only*: document_state and document_relation do not apply, so one combination per control (3);
- *evidence only, no paper*: document_state does not apply (3 × 5 = 15).

3 × 6 × 5 × 5 = 450 combinations, 288 after removing the ones that cannot exist.

## What it can validate

Prototyping data. The inputs look like real requests, but no consultant has confirmed the levels. It can show that the script runs, that the output keeps to the schema, that every axis combination, including the decline case, has rows, and where the system breaks by axis. It cannot support a production accuracy number.

## What it cannot validate

- Other controls. The rows cover 3 controls out of a catalog of more than a hundred, and the implementation scale is different for every control, so results here say nothing about the rest.
- The levels themselves. The generator labelled every row against the catalog and nobody confirmed them. Of the 50 rows checked, one level was too generous and was removed, so others like it are likely still in.
- Real document formats. Every document here is clean text. Real packages contain scans, Word files with tracked changes and long e-mail chains.
- Real package size. Real clients send more and longer documents than these rows, so the sentence that decides the level is harder to find.
- Technical evidence and evidence sent later are not in the data (from the project lead's review).

## What it must never be compared against

The real answers are the consultants' final levels from past client analyses, and the reference assessment the golden levels came from. Both stay inside the firm. These rows are generated and must never be reported as those results or mixed with them in one score.

## Leakage check, outward (what left)

- [x] No real record was used as a seed.
- [x] No real entity names, IDs, or identifiers appear.
- [x] No distinctive internal formats that would identify the firm.
- [x] Rare categories were generated, not copied.

How it was checked: 50 rows spread across all controls and all evidence values, with an automated pre-screen for e-mails, URLs, personal ID numbers, IBANs, phone numbers, company names and code-like references. Nothing of that kind was found. The person names in the rows (for example "Petra Novak") are invented by the generator and do not appear in the golden examples; I checked them against people I know at work and at clients. One code-like reference, `ORG-087`, does not exist in the real catalog. The 16 leak-check hits are schema IDs (`DOC-01`, `CIT-02`, control IDs) and years, not leaks.

Removed after reading:
- 1 row (POL-001, draft later adopted, full evidence): implementation level 5 is too generous; the documents only say implementation has started, and level 5 also needs updates and a yearly effectiveness review.

## Leakage check, inward (what the eval shares with the training data)

**Are the goldens disjoint from anything the system was, or will be, tuned on?**
No, overlap: goldens 3, 5 and 6 were shown to the generator as format examples, so this file and those goldens share a source. If Week 8 tunes on this file, scores on those three goldens are not independent.

**Overlap between `golden.jsonl` and this file, by the dedupe measure:** 0 rows at threshold 0.7 (the closest pair is 0.33).
