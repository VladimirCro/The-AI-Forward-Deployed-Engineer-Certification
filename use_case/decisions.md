# Decision log

One row per architectural decision, with the option you rejected and why.

> **Week 5 asks you to defend your agent architecture against the alternatives.**
> **Week 10's handoff doc is largely this file.** Both are much easier if you
> wrote the reasoning down while you still remembered it.

A decision without a rejected alternative is not a decision, it is a default.
If you cannot name what you did not do, you did not choose.

| Week | Decision | What you rejected | Why | What would change your mind |
| --- | --- | --- | --- | --- |
| 1 | A pipeline, not an agent (1 of 4, answers below the table). Today: `solve()` runs fixed steps (catalog, prompt, one model call, check against `Response`, level statements from the catalog), and the consultant picks the documents. Planned for Week 3: retrieval inside `solve()`, right after the catalog step, so the request carries a client ID instead of pasted documents. Then quotes come from one model call, are checked in code (retried once, then dropped and flagged), and a second call picks the level from the checked quotes only. | An agent that decides its own next step. | The steps are the same every time: statements from the catalog, find quotes, pick a level, and later check the quotes in code. New situations fit the outputs we already have. A pipeline costs the same per request, its output can be compared with the golden examples, and it is easier to get approved. | If the Week 4 evaluation shows that more than 10% of wrong levels come from key evidence that never reached the analysis, add one step where the consultant can send the AI to search again. Only that step, not the whole tool. |
| 1 | Keep the gap report out of the first product. | Building the gap report in TC1. | The consultant's numbers show the self-assessment is about 4 of about 7 consultant-days, so it is the biggest part, and the gap report starts from the consultant's final decision, which the app does not record yet. | If measuring in week 4 shows the assessment is reliable, the gap report becomes the next endpoint. |
| 1 | Golden 6 settled at implementation 3; golden 4 marked unresolved. | Keeping the reference assessment's 3 for golden 4 as settled. | A GRC consultant reviewed the five examples: she agreed with four and called implementation 3 in golden 4 generous. For golden 6 the scale text alone would give 4, because the roles were documented and communicated; she drops it to 3 because the security lead's post is empty and the IT director standing in means IT checks itself. | Agree a coverage threshold for level 3 with the consultants, then settle golden 4. |
| 1 | The output is in Croatian; the instructions to the model are in English. | Everything in English, or translating the output. | The documents and the maturity scale are in Croatian, and the consultant writes the report in Croatian. Quotes have to be word for word, so they cannot be translated. In my vibe check the model translated a Croatian paragraph without being asked and changed its meaning ("until then the policy is not valid" became "at which time the policy will become effective"). The instructions stay in English like the rest of the code. | A client or a market that works in English. Then the rationale and the lists switch to English; the quotes stay in the language of the documents. |
| 2 | Dedupe threshold 0.7 (character 4-gram Jaccard on the request). | Lowering it to 0.4. | Each row is a whole package of documents, so even the closest pair is only 0.49 alike. The pairs above 0.4 look alike in form (the same kinds of documents) but are different cases with different correct levels, so 0.4 would throw away real test cases. At 0.7 nothing was dropped. | Pairs above 0.4 with the same axis combination and the same levels. That is the same case twice, and the threshold goes down to catch it. |
| 2 | Model: `claude-haiku-4-5` through the internal AI gateway. | A local open-weights model (the 350M model from Session 3). | Data has to stay inside the contracted cloud processing [constraint: contract and regulation], and the gateway meets that. The output has to follow the schema [constraint]; the 350M model cannot be steered by instructions and wrote until its token budget ran out, with doubled words [measured, 2026-10-18]. Hosted 3.15 s for an 80-token answer, local 44.8 s on a laptop CPU [measured, 2026-10-18]. Generating this dataset (first run): 288 calls in about 23 minutes, 807k tokens in and 689k out as reported by the provider [measured, 2026-10-20]. $1 per 1M input and $5 per 1M output tokens [looked up; the gateway charges the public price]. No logits and no fixed model version [preference, today]. | A client, auditor or regulator asks for assessments that can be regenerated exactly, consultants ask for a confidence per level, or the provider changes the model and the Week 4 numbers stop holding. Then a self-hosted open-weights model, after the blocked model download on the firm network is solved. |
| 2 | Removed the 6 rows the project lead flagged. | Keeping them because the scenarios are realistic. | The level is not backed by the documents, so the label is wrong. | A consultant agrees with the level. |
| 2 | Relabelled all rows with `claude-opus-5-5` (same documents, new levels) into `synthetic_v2.jsonl`. | Keeping the Haiku levels, or generating everything again with the stronger model. | The project lead found six of twenty Haiku levels the documents do not support, and the new levels agree with that review on all six. Relabelling keeps the documents the same, so the difference comes only from the model, and it costs less than a new generation. | A consultant checks a sample of the new levels and rejects about as many as before. |
| 2 | `synthetic_v2.jsonl` is a record of the relabel test, not the dataset going forward. Before Week 4 the whole set is generated again with a stronger model, and the level statement is filled in by code. | Using v2 as the dataset, or patching it further. | v2 keeps Haiku's documents and fields next to Opus's levels, and 313 rows do not match their recipe. Week 3 uses only the documents, which are the same in v1 and v2. | Week 4 asks for the data in a way that a regenerated set does not fit. |
| 3 | Added `sources` to `Response`. `Request` and `solve()` stay as in Week 1; the new endpoint takes a client and a control, retrieves the client's documents and builds the `Request` from them. | Changing `Request` to a client id instead of documents. | The Week 1 endpoint and the goldens send documents in the `Request`, and Week 4 scores the goldens through `solve()`. Retrieval goes in front of the assessment, not inside it. | Real clients' documents live in a store the request can point to, and nobody pastes documents any more. |
| 3 | Model for the whole app: `claude-sonnet-5-5` through the same gateway, at the provider's default temperature. | Staying with `claude-haiku-4-5`. | The project lead found six of twenty Haiku levels in the Week 2 data that the documents do not support. The retrieval agent also picks its own searches over about 150 documents, a harder job than one call. The model rejects a temperature setting [measured, 2026-10-26], so runs vary: Agentic RAG passed 7 and then 6 of 10 with no change in the code [measured, 2026-10-26]. | Week 4 shows Haiku scores the goldens as well as Sonnet, or the cost per assessment goes over budget. Then Haiku for the steps that pass with it. |
| 3 | <!-- retrieval approach --> | <!-- --> | <!-- --> | <!-- --> |
| 5 | <!-- agent architecture --> | <!-- --> | <!-- --> | <!-- --> |
| 6 | <!-- guardrail level --> | <!-- --> | <!-- --> | <!-- --> |
| 7 | <!-- memory type --> | <!-- --> | <!-- --> | <!-- --> |
| 8 | <!-- model --> | <!-- --> | <!-- --> | <!-- --> |

**Week 1, the four questions.** I answered for the tool as it will be used,
with 50 to 200 documents per client, not only for the Week 1 version where the
consultant picks them. One: the steps do not depend on the input, the flow can
be drawn. Two, yes: with that many documents, something has to search for the
relevant ones. Three: when a quote fails the check, the retry is a fixed rule in
code, not the model's choice. Four: every new case ends in an output the
`Response` already has: a level, no level, a contradiction or missing evidence.

**Week 1, the strongest case for an agent.** Retrieval is planned, not built.
Even with passages instead of whole documents, board minutes can say "the
proposal under item 3 is adopted" without naming the policy, so the sentence
that decides the level may not reach the top results. A consultant who sees
"draft" would go and look for the adoption decision; a fixed pipeline does not
know anything is missing. An agent could notice that, decide it needs another
search and run it.

---

The last column is the one people skip and the one people ask about. "We chose
dense retrieval; we would switch to hybrid if exact-match queries went above ~20%
of traffic" is an engineering position. "We chose dense retrieval" is a
preference.
