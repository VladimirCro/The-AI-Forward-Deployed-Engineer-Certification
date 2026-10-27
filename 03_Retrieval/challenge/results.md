# TC3 retrieval results (2026-10-27)

Model `openai/claude-sonnet-5-5` at the provider's default temperature (the model rejects one), at most 6 tool turns, BM25 top 4 per search (the model may ask for more), one page per document (no chunking inside documents), word split `\w+` so Croatian letters count. Ten fictional clients of about 150 documents each, built by `build_clients.py`; labels in `use_case/evals/retrieval.jsonl`. Dense and hybrid embed with `openai/gemini-embedding-2` through the gateway, one vector per page, one page per call; hybrid fuses the top 50 of BM25 and of dense with RRF k = 60. All three search techniques give the model the same `search_chunks` tool; only the ranking behind it differs.

Embedding tokens for this run: 126,611 [measured, as the endpoint reported them; every page of every client once, plus every dense and hybrid query].

| Technique | Pass | Complete (all gold cited) | Extra documents cited | Calls (mean) | Evidence read, chars (mean) | Latency, s (mean) |
| --- | --- | --- | --- | --- | --- | --- |
| Agentic RAG (BM25) | 6/10 | 5/10 | 42 | 5.1 | 9,219 | 14.3 |
| DCI (wiki) | 8/10 | 8/10 | 22 | 9.1 | 12,842 | 14.6 |
| Dense | 8/10 | 6/10 | 54 | 4.3 | 8,219 | 16.4 |
| Hybrid (BM25 + dense, RRF) | 7/10 | 7/10 | 37 | 5.6 | 10,730 | 22.5 |

| Client | Control | Kind | Technique | Pass | Complete | Extra | Calls | Chars | Latency, s | Stopped |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| klijent-01 | POL-001 | multi-hop | Agentic RAG (BM25) | ✅ | ✅ | 4 | 5 | 9,712 | 18.0 | answer |
| klijent-01 | POL-001 | multi-hop | DCI (wiki) | ✅ | ✅ | 2 | 7 | 11,449 | 17.3 | answer |
| klijent-01 | POL-001 | multi-hop | Dense | ✅ | ❌ | 2 | 5 | 9,727 | 20.5 | answer |
| klijent-01 | POL-001 | multi-hop | Hybrid (BM25 + dense, RRF) | ✅ | ✅ | 3 | 8 | 15,119 | 55.5 | answer |
| klijent-02 | POL-001 | multi-hop | Agentic RAG (BM25) | ✅ | ✅ | 0 | 4 | 7,935 | 10.8 | answer |
| klijent-02 | POL-001 | multi-hop | DCI (wiki) | ✅ | ✅ | 2 | 8 | 11,070 | 12.3 | answer |
| klijent-02 | POL-001 | multi-hop | Dense | ✅ | ❌ | 12 | 4 | 8,776 | 18.2 | answer |
| klijent-02 | POL-001 | multi-hop | Hybrid (BM25 + dense, RRF) | ✅ | ✅ | 0 | 4 | 8,553 | 17.8 | answer |
| klijent-03 | POL-001 | multi-hop | Agentic RAG (BM25) | ✅ | ✅ | 0 | 4 | 7,923 | 11.9 | answer |
| klijent-03 | POL-001 | multi-hop | DCI (wiki) | ✅ | ✅ | 0 | 8 | 11,251 | 12.6 | answer |
| klijent-03 | POL-001 | multi-hop | Dense | ✅ | ✅ | 9 | 3 | 6,176 | 15.7 | answer |
| klijent-03 | POL-001 | multi-hop | Hybrid (BM25 + dense, RRF) | ✅ | ✅ | 1 | 5 | 9,394 | 22.1 | answer |
| klijent-04 | POL-001 | decline | Agentic RAG (BM25) | ❌ | ❌ | 9 | 6 | 8,722 | 8.9 | answer |
| klijent-04 | POL-001 | decline | DCI (wiki) | ❌ | ❌ | 8 | 9 | 15,828 | 17.6 | answer |
| klijent-04 | POL-001 | decline | Dense | ❌ | ❌ | 9 | 5 | 10,454 | 15.7 | answer |
| klijent-04 | POL-001 | decline | Hybrid (BM25 + dense, RRF) | ❌ | ❌ | 6 | 8 | 16,751 | 26.8 | answer |
| klijent-05 | ORG-001 | multi-hop | Agentic RAG (BM25) | ✅ | ✅ | 1 | 4 | 6,751 | 16.7 | answer |
| klijent-05 | ORG-001 | multi-hop | DCI (wiki) | ✅ | ✅ | 0 | 8 | 11,784 | 15.1 | answer |
| klijent-05 | ORG-001 | multi-hop | Dense | ✅ | ✅ | 0 | 4 | 7,115 | 11.4 | answer |
| klijent-05 | ORG-001 | multi-hop | Hybrid (BM25 + dense, RRF) | ✅ | ✅ | 0 | 4 | 7,435 | 16.6 | answer |
| klijent-06 | ORG-001 | multi-hop | Agentic RAG (BM25) | ✅ | ✅ | 0 | 4 | 6,861 | 14.6 | answer |
| klijent-06 | ORG-001 | multi-hop | DCI (wiki) | ✅ | ✅ | 0 | 7 | 11,566 | 15.3 | answer |
| klijent-06 | ORG-001 | multi-hop | Dense | ✅ | ✅ | 0 | 3 | 5,729 | 13.9 | answer |
| klijent-06 | ORG-001 | multi-hop | Hybrid (BM25 + dense, RRF) | ✅ | ✅ | 9 | 3 | 5,415 | 14.2 | answer |
| klijent-07 | ORG-001 | multi-hop | Agentic RAG (BM25) | ❌ | ❌ | 11 | 5 | 9,459 | 18.9 | answer |
| klijent-07 | ORG-001 | multi-hop | DCI (wiki) | ✅ | ✅ | 4 | 19 | 18,463 | 21.4 | answer |
| klijent-07 | ORG-001 | multi-hop | Dense | ✅ | ✅ | 0 | 4 | 7,395 | 20.4 | answer |
| klijent-07 | ORG-001 | multi-hop | Hybrid (BM25 + dense, RRF) | ✅ | ✅ | 4 | 4 | 7,372 | 19.6 | answer |
| klijent-08 | EDU-001 | multi-hop | Agentic RAG (BM25) | ✅ | ❌ | 2 | 6 | 11,178 | 15.1 | answer |
| klijent-08 | EDU-001 | multi-hop | DCI (wiki) | ✅ | ✅ | 2 | 8 | 13,006 | 16.4 | answer |
| klijent-08 | EDU-001 | multi-hop | Dense | ✅ | ✅ | 2 | 4 | 7,631 | 19.9 | answer |
| klijent-08 | EDU-001 | multi-hop | Hybrid (BM25 + dense, RRF) | ✅ | ✅ | 2 | 4 | 7,787 | 17.4 | answer |
| klijent-09 | EDU-001 | multi-hop | Agentic RAG (BM25) | ❌ | ❌ | 8 | 7 | 12,271 | 15.9 | answer |
| klijent-09 | EDU-001 | multi-hop | DCI (wiki) | ✅ | ✅ | 4 | 5 | 11,252 | 8.4 | answer |
| klijent-09 | EDU-001 | multi-hop | Dense | ✅ | ✅ | 2 | 4 | 7,107 | 10.1 | answer |
| klijent-09 | EDU-001 | multi-hop | Hybrid (BM25 + dense, RRF) | ❌ | ❌ | 5 | 8 | 14,034 | 18.8 | answer |
| klijent-10 | EDU-001 | decline | Agentic RAG (BM25) | ❌ | ❌ | 7 | 6 | 11,381 | 11.8 | answer |
| klijent-10 | EDU-001 | decline | DCI (wiki) | ❌ | ❌ | 0 | 12 | 12,753 | 9.3 | max_turns |
| klijent-10 | EDU-001 | decline | Dense | ❌ | ❌ | 18 | 7 | 12,083 | 18.1 | answer |
| klijent-10 | EDU-001 | decline | Hybrid (BM25 + dense, RRF) | ❌ | ❌ | 7 | 8 | 15,436 | 16.3 | answer |

## Range over seven runs

The model runs at the provider's default temperature, so the same code gives a slightly different result each run. Seven runs on 2026-10-27, while the noise in the clients was cleaned twice: noise documents that were evidence under another word ("obaviješteni", "izjava", "test znanja" for EDU-001; "Direktiva" for POL-001) were taken out. Each cleaning touched one control's clients, and every technique ran on the same pages in every run. The table above is the last run, on the final pages.

| Technique | Pass | Complete | Extra documents cited | Calls (mean) |
| --- | --- | --- | --- | --- |
| Agentic RAG (BM25) | 5 to 7 | 5 to 6 | 32 to 46 | 5.1 to 5.7 |
| DCI (wiki) | 8 | 8 | 14 to 25 | 8.3 to 9.9 |
| Dense | 7 to 8 | 5 to 6 | 43 to 77 | 4.1 to 4.6 |
| Hybrid (BM25 + dense, RRF) | 6 to 8 | 5 to 7 | 29 to 46 | 4.8 to 5.6 |

Hybrid was never below the better of BM25 and dense on complete, and above both in five of seven runs. Embedding tokens were about 126,400 per run [measured].
