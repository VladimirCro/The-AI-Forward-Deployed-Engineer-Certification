# TC3 endpoint on the ten cases (2026-10-27)

`assess_control_for_client`: hybrid retrieval, one call that labels each document supports, contradicts or neutral, `solve()` on the supporting and contradicting ones, every quote checked against its document. Correct means: a decline case returns no level and no sources; any other case has every gold document in `sources`. Extra counts the sources that are not gold.

Same model and retrieval settings as `results.md`: `openai/claude-sonnet-5-5`, hybrid search with RRF k = 60, top 4 per search, at most 6 tool turns.

Correct: 9/10.

| Client | Control | Kind | Documentation | Implementation | Sources | Gold in sources | Extra | Correct | Latency, s |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| klijent-01 | POL-001 | multi-hop | 2 | 3 | r12-DOC-07, r12-DOC-08, r12-DOC-09 | 3/3 | 0 | ✅ | 91.5 |
| klijent-02 | POL-001 | multi-hop | 3 | 3 | r24-DOC-01, r24-DOC-02, r24-DOC-03 | 3/3 | 0 | ✅ | 85.7 |
| klijent-03 | POL-001 | multi-hop | 3 | 4 | r34-DOC-01, r34-DOC-02, r34-DOC-03 | 3/3 | 0 | ✅ | 80.8 |
| klijent-04 | POL-001 | decline | - | - | none | n/a | 0 | ✅ | 62.4 |
| klijent-05 | ORG-001 | multi-hop | 4 | 4 | r174-DOC-01, r174-DOC-02, r174-DOC-03, r174-DOC-04 | 4/4 | 0 | ✅ | 66.3 |
| klijent-06 | ORG-001 | multi-hop | 4 | 4 | r189-DOC-01, r189-DOC-03, r189-DOC-04, r189-DOC-02 | 4/4 | 0 | ✅ | 71.1 |
| klijent-07 | ORG-001 | multi-hop | 3 | 3 | r300-DOC-01, r300-DOC-04, r300-DOC-02, r300-DOC-03 | 4/4 | 0 | ✅ | 71.4 |
| klijent-08 | EDU-001 | multi-hop | 3 | 3 | r350-DOC-01, r350-DOC-02, r350-DOC-03 | 3/3 | 0 | ✅ | 70.4 |
| klijent-09 | EDU-001 | multi-hop | 2 | 2 | r378-DOC-01, r378-DOC-02, r299-DOC-04, r214-DOC-03 | 2/2 | 2 | ✅ | 56.8 |
| klijent-10 | EDU-001 | decline | - | 2 | r294-DOC-03, r315-DOC-02, r336-DOC-04, r284-DOC-03 | n/a | 4 | ❌ | 63.5 |

## Range over three runs

| Run | Correct | Multi-hop cases with every gold document | klijent-04 declined | klijent-10 declined |
| --- | --- | --- | --- | --- |
| 1 | 6/10 | 6 of 8 | no: a draft rulebook from ORG-001 noise was labelled as supporting | no |
| 2 | 8/10 | 7 of 8 | yes | no |
| 3 | 9/10 | 8 of 8 | yes | no |

The table above is run 3. klijent-10 is explained in `## Retrieval notes` in the README.
