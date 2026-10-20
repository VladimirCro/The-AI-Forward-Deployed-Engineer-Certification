# Decision log

One row per architectural decision, with the option you rejected and why.

> **Week 5 asks you to defend your agent architecture against the alternatives.**
> **Week 10's handoff doc is largely this file.** Both are much easier if you
> wrote the reasoning down while you still remembered it.

A decision without a rejected alternative is not a decision, it is a default.
If you cannot name what you did not do, you did not choose.

| Week | Decision | What you rejected | Why | What would change your mind |
| --- | --- | --- | --- | --- |
| 1 | A pipeline, not an agent (1 of 4). Retrieval is a fixed step in front of `solve()`. A quote that fails the check is retried once, then dropped and flagged. | An agent that decides its own next step. | The steps are the same every time: statements from the catalog, find quotes, check them in code, pick a level. New situations fit the outputs we already have. A pipeline costs the same per request, its output can be compared with the golden examples, and it is easier to get approved. | If the Week 4 evaluation shows that more than 10% of wrong levels come from key evidence that never reached the analysis, add one step where the consultant can send the AI to search again. Only that step, not the whole tool. |
| 1 | Keep the gap report out of the first product. | Building the gap report in TC1. | The consultant's numbers show the self-assessment is about 4 of about 7 consultant-days, so it is the biggest part, and the gap report starts from the consultant's final decision, which the app does not record yet. | If measuring in week 4 shows the assessment is reliable, the gap report becomes the next endpoint. |
| 1 | Golden 6 settled at implementation 3; golden 4 marked unresolved. | Keeping the reference assessment's 3 for golden 4 as settled. | A GRC consultant reviewed the five examples: she agreed with four and called implementation 3 in golden 4 generous. | Agree a coverage threshold for level 3 with the consultants, then settle golden 4. |
| 2 | Dedupe threshold 0.7 (character 4-gram Jaccard on the request). | Lowering it to 0.4. | Each row is a whole package of documents, so even the closest pair is only 0.49 alike. The pairs above 0.4 look alike in form (the same kinds of documents) but are different cases with different correct levels, so 0.4 would throw away real test cases. At 0.7 nothing was dropped. | Pairs above 0.4 with the same axis combination and the same levels. That is the same case twice, and the threshold goes down to catch it. |
| 2 | Model: `claude-haiku-4-5` through the internal AI gateway. | A local open-weights model (the 350M model from Session 3). | Data has to stay inside the contracted cloud processing [constraint: contract and regulation], and the gateway meets that. The output has to follow the schema [constraint]; the 350M model cannot be steered by instructions and wrote until its token budget ran out, with doubled words [measured, 2026-10-18]. Hosted 3.15 s for an 80-token answer, local 44.8 s on a laptop CPU [measured, 2026-10-18]. Generating this dataset (first run): 288 calls in about 23 minutes, 807k tokens in and 689k out as reported by the provider [measured, 2026-10-20]. $1 per 1M input and $5 per 1M output tokens [looked up; the gateway charges the public price]. No logits and no fixed model version [preference, today]. | A client, auditor or regulator asks for assessments that can be regenerated exactly, consultants ask for a confidence per level, or the provider changes the model and the Week 4 numbers stop holding. Then a self-hosted open-weights model, after the blocked model download on the firm network is solved. |
| 2 | Removed the 6 rows the project lead flagged. | Keeping them because the scenarios are realistic. | The level is not backed by the documents, so the label is wrong. | A consultant agrees with the level. |
| 3 | <!-- retrieval approach --> | <!-- --> | <!-- --> | <!-- --> |
| 5 | <!-- agent architecture --> | <!-- --> | <!-- --> | <!-- --> |
| 6 | <!-- guardrail level --> | <!-- --> | <!-- --> | <!-- --> |
| 7 | <!-- memory type --> | <!-- --> | <!-- --> | <!-- --> |
| 8 | <!-- model --> | <!-- --> | <!-- --> | <!-- --> |

**Week 1, the strongest case for an agent.** Documents are indexed whole, so a
long document such as board minutes, with one relevant sentence among many
other topics, may not reach the top results, and the evidence that decides the
level never gets to the analysis. A consultant who sees "draft" would go and
look for the adoption decision; a fixed pipeline does not know anything is
missing. An agent could notice that, decide it needs another search and run it.

---

The last column is the one people skip and the one people ask about. "We chose
dense retrieval; we would switch to hybrid if exact-match queries went above ~20%
of traffic" is an engineering position. "We chose dense retrieval" is a
preference.
