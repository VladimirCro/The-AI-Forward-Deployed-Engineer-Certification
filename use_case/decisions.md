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

The last column is the one people skip and the one clients ask about. "We chose
dense retrieval; we would switch to hybrid if exact-match queries went above ~20%
of traffic" is an engineering position. "We chose dense retrieval" is a
preference.
