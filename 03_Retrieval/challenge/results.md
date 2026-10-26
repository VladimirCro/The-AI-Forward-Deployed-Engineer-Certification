# TC3 retrieval results (2026-10-26)

Model `openai/claude-sonnet-5-5` at the provider's default temperature (the model rejects one), at most 6 tool turns, BM25 top 4 per search (the model may ask for more), one page per document (no chunking inside documents), word split `\w+` so Croatian letters count. Ten fictional clients of about 150 documents each, built by `build_clients.py`; labels in `use_case/evals/retrieval.jsonl`.

| Technique | Pass | Complete (all gold cited) | Extra documents cited | Calls (mean) | Evidence read, chars (mean) | Latency, s (mean) |
| --- | --- | --- | --- | --- | --- | --- |
| Agentic RAG (BM25) | 6/10 | 6/10 | 37 | 5.7 | 10,663 | 14.2 |
| DCI (wiki) | 8/10 | 8/10 | 22 | 8.5 | 12,217 | 12.6 |

| Client | Control | Kind | Technique | Pass | Complete | Extra | Calls | Chars | Latency, s | Stopped |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| klijent-01 | POL-001 | multi-hop | Agentic RAG (BM25) | ✅ | ✅ | 3 | 6 | 11,495 | 20.2 | answer |
| klijent-01 | POL-001 | multi-hop | DCI (wiki) | ✅ | ✅ | 2 | 8 | 12,190 | 16.3 | answer |
| klijent-02 | POL-001 | multi-hop | Agentic RAG (BM25) | ✅ | ✅ | 2 | 5 | 9,687 | 17.6 | answer |
| klijent-02 | POL-001 | multi-hop | DCI (wiki) | ✅ | ✅ | 1 | 8 | 11,070 | 10.4 | answer |
| klijent-03 | POL-001 | multi-hop | Agentic RAG (BM25) | ❌ | ✅ | 0 | 4 | 7,838 | 12.5 | answer |
| klijent-03 | POL-001 | multi-hop | DCI (wiki) | ✅ | ✅ | 3 | 8 | 11,121 | 11.8 | answer |
| klijent-04 | POL-001 | decline | Agentic RAG (BM25) | ❌ | ❌ | 9 | 9 | 18,071 | 15.7 | answer |
| klijent-04 | POL-001 | decline | DCI (wiki) | ❌ | ❌ | 7 | 10 | 12,114 | 14.0 | answer |
| klijent-05 | ORG-001 | multi-hop | Agentic RAG (BM25) | ✅ | ✅ | 1 | 3 | 5,248 | 11.3 | answer |
| klijent-05 | ORG-001 | multi-hop | DCI (wiki) | ✅ | ✅ | 0 | 9 | 11,688 | 13.4 | answer |
| klijent-06 | ORG-001 | multi-hop | Agentic RAG (BM25) | ✅ | ✅ | 0 | 4 | 6,929 | 11.1 | answer |
| klijent-06 | ORG-001 | multi-hop | DCI (wiki) | ✅ | ✅ | 0 | 7 | 11,769 | 10.4 | answer |
| klijent-07 | ORG-001 | multi-hop | Agentic RAG (BM25) | ✅ | ✅ | 4 | 5 | 9,219 | 12.6 | answer |
| klijent-07 | ORG-001 | multi-hop | DCI (wiki) | ✅ | ✅ | 1 | 10 | 14,245 | 14.0 | answer |
| klijent-08 | EDU-001 | multi-hop | Agentic RAG (BM25) | ✅ | ❌ | 4 | 5 | 8,925 | 10.9 | answer |
| klijent-08 | EDU-001 | multi-hop | DCI (wiki) | ✅ | ✅ | 2 | 6 | 13,128 | 10.5 | answer |
| klijent-09 | EDU-001 | multi-hop | Agentic RAG (BM25) | ❌ | ❌ | 5 | 8 | 15,214 | 14.6 | answer |
| klijent-09 | EDU-001 | multi-hop | DCI (wiki) | ✅ | ✅ | 0 | 5 | 12,181 | 8.8 | answer |
| klijent-10 | EDU-001 | decline | Agentic RAG (BM25) | ❌ | ❌ | 9 | 8 | 14,004 | 15.6 | answer |
| klijent-10 | EDU-001 | decline | DCI (wiki) | ❌ | ❌ | 6 | 14 | 12,667 | 16.5 | answer |
