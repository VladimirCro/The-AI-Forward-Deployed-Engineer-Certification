# TC3 endpoint on the ten cases (2026-10-27)

`assess_control_for_client`: hybrid retrieval, one call that labels each document supports, contradicts or neutral, `solve()` on the supporting and contradicting ones, every quote checked against its document. Correct means: a decline case returns no level and no sources; any other case has every gold document in `sources`.

Correct: 9/10.

| Client | Control | Kind | Documentation | Implementation | Sources | Gold in sources | Correct | Latency, s |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| klijent-01 | POL-001 | multi-hop | - | 3 | r12-DOC-07, r12-DOC-08, r12-DOC-09 | 3/3 | ✅ | 98.2 |
| klijent-02 | POL-001 | multi-hop | 3 | 3 | r24-DOC-01, r24-DOC-03, r24-DOC-02 | 3/3 | ✅ | 83.7 |
| klijent-03 | POL-001 | multi-hop | 3 | 4 | r34-DOC-01, r34-DOC-02, r34-DOC-03 | 3/3 | ✅ | 80.5 |
| klijent-04 | POL-001 | decline | - | - | none | n/a | ✅ | 59.2 |
| klijent-05 | ORG-001 | multi-hop | 4 | 4 | r174-DOC-01, r174-DOC-02, r174-DOC-03, r174-DOC-04 | 4/4 | ✅ | 73.5 |
| klijent-06 | ORG-001 | multi-hop | 4 | 4 | r189-DOC-01, r189-DOC-03, r189-DOC-04, r189-DOC-02 | 4/4 | ✅ | 73.9 |
| klijent-07 | ORG-001 | multi-hop | 2 | 3 | r300-DOC-01, r300-DOC-03, r300-DOC-02, r300-DOC-04, r110-DOC-01, r105-DOC-05, r121-DOC-03, r125-DOC-01 | 4/4 | ✅ | 91.8 |
| klijent-08 | EDU-001 | multi-hop | 3 | 3 | r350-DOC-01, r350-DOC-02, r350-DOC-03, r72-DOC-14, r299-DOC-04, r202-DOC-04 | 3/3 | ✅ | 77.5 |
| klijent-09 | EDU-001 | multi-hop | 2 | 2 | r378-DOC-01, r378-DOC-02, r299-DOC-04, r145-DOC-01 | 2/2 | ✅ | 60.7 |
| klijent-10 | EDU-001 | decline | 2 | 2 | r43-DOC-03, r43-DOC-01, r294-DOC-03 | n/a | ❌ | 59.1 |
