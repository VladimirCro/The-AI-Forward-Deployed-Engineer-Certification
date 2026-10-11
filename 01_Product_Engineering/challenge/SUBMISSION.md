# Week 1 submission

## Step 7 — Golden examples

Example 3 is the edge case (two documents disagree), example 5 is the decline
(no relevant evidence, no level). Example 6 is unresolved.

## Step 8 — The endpoint

**1. What is one thing you do at work this could take over?**
Reading the client's evidence documents for one control and picking which of
the five prescribed statements they support, for documentation and for
implementation. Today a GRC consultant spends about 14 minutes per control on
this, across 137 controls per client.

**2. What exactly goes in — a string, a file, several fields?**
Two fields: a control ID from the catalog (for example `POL-001`), and a list of
evidence documents, each with an ID, a name and its text. The text is pasted in,
not uploaded as a file. The five plus five statements for the control come from
the tool's own catalog, not from the caller.

**3. What comes back, and who reads it?**
A JSON object that matches the `Response` type: a proposed level for
documentation and for implementation (or no level when the evidence is
insufficient), quotes from the documents, a short rationale, contradictions and
missing evidence. The GRC consultant reads it and makes the final decision.

**4. What did you name it, and why would an agent pick it correctly?**
`propose_control_maturity`, because the tool proposes and the consultant
decides. The verb says it only proposes, and the object says it works on one
control's maturity level.
