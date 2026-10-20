# Datasheet

<!-- Written in TC2, alongside your synthetic data. This file is committed; the
     data itself is not. -->

## What this data is

**Generated on:** <!-- date -->
**Generated from:** <!-- the schema + a written description, NOT real records -->
**Rows:** <!-- n -->

## Variation axes

The same list as `02_Open_Weights/challenge/axes.py`. One request is one control plus the client's evidence documents.

| Axis | Values | Why |
| --- | --- | --- |
| control | POL-001 (top-level cybersecurity policy) · ORG-001 (roles, responsibilities and duties) · EDU-001 (staff awareness training) | The system must work on every topic, and the implementation scale is different for each control. |
| document_state | adopted and in force · draft · not adopted or not signed · incomplete (a section or annex is missing) · badly or vaguely worded · outdated (adopted, but not reviewed for years) | Good content does not make a document valid; the catalog separates adopted, up to date and complete (golden 1, 2). |
| document_relation | documents agree · documents contradict each other · several versions of the same document · a later event changes the situation · refers to a document that was not submitted | The system has to know which document is authoritative and notice what is missing (golden 3, 6). |
| implementation_evidence | full evidence · partial evidence, near a level threshold · paper only, no evidence of implementation · evidence only, no paper · irrelevant documents only (decline: no level, ask for evidence) | Implementation must not be inferred from paper, and without relevant evidence there is no level (golden 4, 5). |

Combinations that cannot exist are removed before generation:
- *irrelevant documents only*: document_state and document_relation do not apply, so one combination per control (3);
- *evidence only, no paper*: document_state does not apply (3 × 5 = 15).

3 × 6 × 5 × 5 = 450 combinations, 288 after removing the ones that cannot exist.

## What it can validate

<!-- Which claims this data supports. Be narrow. -->

## What it cannot validate

<!-- The important half. Synthetic data cannot tell you about real distribution,
     real frequency, or failure modes you did not think to generate. Say so. -->

## What it must never be compared against

<!-- If you have real ground truth somewhere, say where, and say explicitly that
     these rows are not it. -->

## Leakage check — outward (what left)

- [ ] No real record was used as a seed.
- [ ] No real entity names, IDs, or identifiers appear.
- [ ] No distinctive internal formats that would identify the firm.
- [ ] Rare categories were generated, not copied.

## Leakage check — inward (what the eval shares with the training data)

**Are the goldens disjoint from anything the system was, or will be, tuned on?**
<!-- yes, disjoint | no — overlap: <which goldens, which source> | unknown — who would know: <role> -->

**Overlap between `golden.jsonl` and this file, by the dedupe measure:** <!-- n rows at threshold t -->
