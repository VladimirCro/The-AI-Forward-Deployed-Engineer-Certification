# Project charter

<!--
  Fill this in during TC1, from your Getting to Concreteness worksheet.
  Every week's Session 2 notebook reads this file and stops if it is still the
  template. That is on purpose.
-->

**Department:** IT security consulting — governance, risk and compliance (GRC)

**Working title:** Evidence-to-Maturity Assistant

---

## The problem

**Who has it?** One real role, not a department.

A GRC consultant (governance, risk and compliance) in an IT security consulting
team: a mid-to-senior information security professional with audit experience,
familiar with ISO 27001 and the national cybersecurity law, handling several
client organisations at once. Today they feel under constant time pressure,
spend most of their time reading documents and filling spreadsheets instead of
advising, and worry about consistency because their assessment must hold up in
an audit.

**What are they trying to do?**

Carry out the mandatory cybersecurity self-assessment for a client organisation
covered by the national cybersecurity law (the EU NIS2 transposition): for every
control in the regulator's official calculator, decide which of five prescribed
maturity statements the client's evidence supports — once for documentation and
once for implementation — with a justification that holds up in an audit.

**How do they handle it today?**

They collect the client's evidence documents (policies, board minutes,
rulebooks, role assignments, training reports) by email and in interviews. For
each control in the regulator's Excel calculator they read the relevant
documents, find the passages that support or contradict the control, and pick
one of the five prescribed statements for documentation and one for
implementation; the calculator then computes the scores. The gap report and
implementation plan are written by hand.

**What does that cost — time, money, risk, or relationships?**

About 4 consultant-days (~32 hours) per client, most of it reading evidence and
filling the calculator. Demand from organisations obliged by the law is higher
than the team's capacity and the deadline is fixed, so clients the team cannot
serve in time go to competitors — lost for this assessment and for the
follow-up work. Manual, judgement-heavy work also means two consultants can
reach different conclusions on the same evidence, which is an audit risk.

**The problem in one sentence. No solution in it.**

Deciding, for every control, which prescribed maturity level a client's
evidence supports takes a GRC consultant about four days per client, so the
team cannot keep up with organisations that must self-assess by law.

---

## Success

**What does the new world look like for that person?**

The consultant opens a control and already sees a proposed maturity statement
for documentation and for implementation, each backed by verbatim quotes from
the client's documents, plus any contradictions and missing evidence. They
accept, change or reject it; the score is computed from their decision, never by
the AI. Their time goes to borderline cases, talking to the client and advising
on remediation instead of reading every document.

**How would the firm measure it? Which numbers should move?**

- Consultant time per client: from ~4 days to ~1 day.
- Clients served per consultant per month: up to four times more.
- Agreement between the proposed level and the consultant's final decision.
- Unsupported citations (quotes not found in the source): zero.
- Correct declines: when evidence is missing, no level is proposed.

---

## The first product

**Your solution in one sentence.**

An assistant for GRC consultants that reads a client's evidence documents and,
for each of three controls from the regulator's calculator, proposes one of the
five prescribed maturity statements for documentation and for implementation,
with verbatim citations, contradictions and missing evidence, so the consultant
can decide in minutes instead of hours.

**Input → Output.** Be specific enough that someone could build it wrong and you
would notice.

| | |
| --- | --- |
| **In** | A control ID (e.g. `POL-001`) with its five documentation and five implementation statements from the public calculator, and 1–N evidence documents as plain text, each with an ID (e.g. `DOC-02`) and a name. |
| **Out** | For documentation and for implementation separately: the proposed level 1–5, or **no level** with the reason "insufficient evidence"; verbatim quotes, each with document ID and location, that must exist in the input; a one-to-two sentence rationale. Plus a list of contradictions between documents and a list of missing evidence. Never a final score — the consultant decides. |

---

## Decisions made later

<!--
  Amended as the cohort goes. Keep the reasoning, not just the choice — Week 5
  asks you to defend your architecture against the options you rejected, and
  Week 10's handoff doc is largely this section.
-->

| Week | Decision | Why, and what you rejected |
| --- | --- | --- |
| 3 | Retrieval approach | <!-- TC3 --> |
| 5 | Agent architecture | <!-- TC5 --> |
| 8 | Model | <!-- TC8 --> |
