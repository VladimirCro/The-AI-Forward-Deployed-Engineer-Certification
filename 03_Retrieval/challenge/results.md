# TC3 retrieval results (2026-10-27)

Model `openai/claude-sonnet-5-5` at the provider's default temperature (the model does not accept a temperature setting), at most 6 tool turns, top 4 per search for BM25, dense and hybrid (the model may ask for up to 8), one page per document (no chunking inside documents), word split `\w+` so Croatian letters count. Ten fictional clients of about 150 documents each, built by `build_clients.py`; labels in `use_case/evals/retrieval.jsonl`. Dense and hybrid embed with `openai/gemini-embedding-2` through the gateway, one vector per page, one page per call; hybrid fuses the top 50 of BM25 and of dense with RRF k = 60. All three search techniques give the model the same `search_chunks` tool; only the ranking behind it differs. Noise documents that mention the control's topic are left out of each client, so the test is easier than a real client folder, most of all for keyword search.

Pass: every reviewed term from `retrieval.jsonl` appears in the answer. Complete: every gold document is cited. A decline case passes only if the agent answers "no evidence found" and cites no document. No technique declined on its own, which is why the endpoint labels the documents in a separate step.

Embedding tokens for this run: 126,408 [measured, as the endpoint reported them; every page of every client once, plus every dense and hybrid query].

| Technique | Pass | Complete (all gold cited) | Extra documents cited | Calls (mean) | Evidence read, chars (mean) | Latency, s (mean) |
| --- | --- | --- | --- | --- | --- | --- |
| Agentic RAG (BM25) | 6/10 | 6/10 | 42 | 5.4 | 9,997 | 13.1 |
| DCI (wiki) | 8/10 | 8/10 | 11 | 9.3 | 12,532 | 13.1 |
| Dense | 8/10 | 7/10 | 39 | 4.2 | 7,978 | 12.4 |
| Hybrid (BM25 + dense, RRF) | 8/10 | 8/10 | 35 | 4.7 | 9,310 | 14.5 |

| Client | Control | Kind | Technique | Pass | Complete | Extra | Calls | Chars | Latency, s | Stopped |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| klijent-01 | POL-001 | multi-hop | Agentic RAG (BM25) | ✅ | ✅ | 2 | 5 | 9,682 | 13.0 | answer |
| klijent-01 | POL-001 | multi-hop | DCI (wiki) | ✅ | ✅ | 3 | 10 | 12,126 | 17.0 | answer |
| klijent-01 | POL-001 | multi-hop | Dense | ✅ | ❌ | 11 | 4 | 7,403 | 12.3 | answer |
| klijent-01 | POL-001 | multi-hop | Hybrid (BM25 + dense, RRF) | ✅ | ✅ | 3 | 7 | 14,227 | 28.8 | answer |
| klijent-02 | POL-001 | multi-hop | Agentic RAG (BM25) | ✅ | ✅ | 0 | 4 | 7,922 | 10.9 | answer |
| klijent-02 | POL-001 | multi-hop | DCI (wiki) | ✅ | ✅ | 2 | 10 | 11,721 | 12.4 | answer |
| klijent-02 | POL-001 | multi-hop | Dense | ✅ | ✅ | 0 | 5 | 10,506 | 11.8 | answer |
| klijent-02 | POL-001 | multi-hop | Hybrid (BM25 + dense, RRF) | ✅ | ✅ | 0 | 5 | 10,407 | 13.5 | answer |
| klijent-03 | POL-001 | multi-hop | Agentic RAG (BM25) | ✅ | ✅ | 0 | 4 | 7,662 | 10.3 | answer |
| klijent-03 | POL-001 | multi-hop | DCI (wiki) | ✅ | ✅ | 1 | 8 | 12,814 | 12.9 | answer |
| klijent-03 | POL-001 | multi-hop | Dense | ✅ | ✅ | 1 | 5 | 10,378 | 11.6 | answer |
| klijent-03 | POL-001 | multi-hop | Hybrid (BM25 + dense, RRF) | ✅ | ✅ | 6 | 3 | 6,281 | 10.6 | answer |
| klijent-04 | POL-001 | decline | Agentic RAG (BM25) | ❌ | ❌ | 11 | 6 | 12,189 | 9.3 | answer |
| klijent-04 | POL-001 | decline | DCI (wiki) | ❌ | ❌ | 0 | 13 | 16,983 | 11.8 | max_turns |
| klijent-04 | POL-001 | decline | Dense | ❌ | ❌ | 10 | 5 | 10,439 | 9.4 | answer |
| klijent-04 | POL-001 | decline | Hybrid (BM25 + dense, RRF) | ❌ | ❌ | 2 | 6 | 12,871 | 9.1 | answer |
| klijent-05 | ORG-001 | multi-hop | Agentic RAG (BM25) | ✅ | ✅ | 3 | 4 | 6,991 | 15.8 | answer |
| klijent-05 | ORG-001 | multi-hop | DCI (wiki) | ✅ | ✅ | 2 | 9 | 11,658 | 17.9 | answer |
| klijent-05 | ORG-001 | multi-hop | Dense | ✅ | ✅ | 3 | 4 | 7,530 | 13.2 | answer |
| klijent-05 | ORG-001 | multi-hop | Hybrid (BM25 + dense, RRF) | ✅ | ✅ | 0 | 4 | 7,432 | 11.0 | answer |
| klijent-06 | ORG-001 | multi-hop | Agentic RAG (BM25) | ✅ | ✅ | 1 | 4 | 6,918 | 10.6 | answer |
| klijent-06 | ORG-001 | multi-hop | DCI (wiki) | ✅ | ✅ | 0 | 7 | 11,711 | 12.1 | answer |
| klijent-06 | ORG-001 | multi-hop | Dense | ✅ | ✅ | 0 | 3 | 5,661 | 11.4 | answer |
| klijent-06 | ORG-001 | multi-hop | Hybrid (BM25 + dense, RRF) | ✅ | ✅ | 4 | 3 | 5,567 | 10.7 | answer |
| klijent-07 | ORG-001 | multi-hop | Agentic RAG (BM25) | ❌ | ✅ | 2 | 5 | 8,518 | 12.4 | answer |
| klijent-07 | ORG-001 | multi-hop | DCI (wiki) | ✅ | ✅ | 1 | 11 | 13,161 | 17.4 | answer |
| klijent-07 | ORG-001 | multi-hop | Dense | ✅ | ✅ | 0 | 3 | 5,215 | 12.0 | answer |
| klijent-07 | ORG-001 | multi-hop | Hybrid (BM25 + dense, RRF) | ✅ | ✅ | 5 | 3 | 5,756 | 17.4 | answer |
| klijent-08 | EDU-001 | multi-hop | Agentic RAG (BM25) | ✅ | ❌ | 3 | 5 | 9,736 | 14.7 | answer |
| klijent-08 | EDU-001 | multi-hop | DCI (wiki) | ✅ | ✅ | 0 | 6 | 10,797 | 11.1 | answer |
| klijent-08 | EDU-001 | multi-hop | Dense | ✅ | ✅ | 2 | 4 | 7,484 | 19.8 | answer |
| klijent-08 | EDU-001 | multi-hop | Hybrid (BM25 + dense, RRF) | ✅ | ✅ | 3 | 5 | 9,790 | 20.8 | answer |
| klijent-09 | EDU-001 | multi-hop | Agentic RAG (BM25) | ❌ | ❌ | 9 | 9 | 16,342 | 19.4 | answer |
| klijent-09 | EDU-001 | multi-hop | DCI (wiki) | ✅ | ✅ | 2 | 6 | 11,748 | 8.7 | answer |
| klijent-09 | EDU-001 | multi-hop | Dense | ✅ | ✅ | 4 | 3 | 5,190 | 8.2 | answer |
| klijent-09 | EDU-001 | multi-hop | Hybrid (BM25 + dense, RRF) | ✅ | ✅ | 2 | 6 | 11,120 | 13.9 | answer |
| klijent-10 | EDU-001 | decline | Agentic RAG (BM25) | ❌ | ❌ | 11 | 8 | 14,011 | 14.8 | answer |
| klijent-10 | EDU-001 | decline | DCI (wiki) | ❌ | ❌ | 0 | 13 | 12,600 | 10.1 | max_turns |
| klijent-10 | EDU-001 | decline | Dense | ❌ | ❌ | 8 | 6 | 9,974 | 14.6 | answer |
| klijent-10 | EDU-001 | decline | Hybrid (BM25 + dense, RRF) | ❌ | ❌ | 10 | 5 | 9,645 | 9.5 | answer |

## Range over three runs on the final pages

The model takes no temperature, so the same code gives a slightly different result each run. The table above is the third of these runs.

| Technique | Pass | Complete | Extra documents cited | Calls (mean) | Evidence read, chars (mean) |
| --- | --- | --- | --- | --- | --- |
| Agentic RAG (BM25) | 6 to 8 | 6 to 7 | 29 to 42 | 4.9 to 5.4 | 9,165 to 9,997 |
| DCI (wiki) | 7 to 8 | 7 to 8 | 11 to 16 | 9.2 to 9.8 | 12,532 to 12,886 |
| Dense | 6 to 8 | 5 to 7 | 39 to 53 | 4.1 to 4.2 | 7,880 to 8,145 |
| Hybrid (BM25 + dense, RRF) | 7 to 8 | 7 to 8 | 35 to 46 | 4.7 to 5.2 | 9,310 to 10,130 |

Embedding tokens were 126,384 to 126,536 per run [measured], pages plus search queries.

BM25 and dense miss different documents. In the table above, BM25 cites every gold document for klijent-01 and dense does not; for klijent-08 and klijent-09 it is the other way round. Hybrid gets all three.

## Every run on 2026-10-27

Complete, out of 10. Before the final pages I took noise documents out of the clients three times, because some of them were real evidence in other words ("obaviješteni", "izjava", "test znanja" for EDU-001, "Direktiva" for POL-001, "odgovoran" for ORG-001). Every technique ran on the same pages in every run.

| Run | Pages | BM25 | DCI | Dense | Hybrid |
| --- | --- | --- | --- | --- | --- |
| 1 | EDU noise cleaned once | 6 | 8 | 6 | 7 |
| 2 | same | 5 | 8 | 6 | 7 |
| 3 | same | 6 | 8 | 6 | 7 |
| 4 | EDU noise cleaned twice | 6 | 8 | 6 | 7 |
| 5 | same | 6 | 8 | 6 | 6 |
| 6 | same | 5 | 8 | 5 | 5 |
| 7 | POL noise cleaned | 5 | 8 | 6 | 7 |
| 8 | ORG noise cleaned (final) | 7 | 7 | 5 | 7 |
| 9 | final | 6 | 7 | 6 | 7 |
| 10 | final | 6 | 8 | 7 | 8 |

Hybrid was never below the better of BM25 and dense on complete, and above both in seven of the ten runs.
