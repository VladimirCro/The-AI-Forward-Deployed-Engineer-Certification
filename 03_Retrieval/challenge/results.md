# TC3 retrieval results (2026-10-26)

Model `openai/claude-sonnet-5-5` at the provider's default temperature (the model rejects one), at most 6 tool turns, BM25 top 4 per search (the model may ask for more), one page per document (no chunking inside documents), word split `\w+` so Croatian letters count. Ten fictional clients of about 150 documents each, built by `build_clients.py`; labels in `use_case/evals/retrieval.jsonl`.

| Technique | Pass | Complete (all gold cited) | Extra documents cited | Calls (mean) | Evidence read, chars (mean) | Latency, s (mean) |
| --- | --- | --- | --- | --- | --- | --- |
| Agentic RAG (BM25) | 7/10 | 6/10 | 41 | 5.5 | 10,316 | 13.7 |
| DCI (wiki) | 8/10 | 8/10 | 22 | 9.3 | 13,170 | 12.8 |

| Client | Control | Kind | Technique | Pass | Complete | Extra | Calls | Chars | Latency, s | Stopped |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| klijent-01 | POL-001 | multi-hop | Agentic RAG (BM25) | ✅ | ✅ | 2 | 5 | 9,662 | 17.1 | answer |
| klijent-01 | POL-001 | multi-hop | DCI (wiki) | ✅ | ✅ | 2 | 7 | 10,843 | 12.9 | answer |
| klijent-02 | POL-001 | multi-hop | Agentic RAG (BM25) | ✅ | ✅ | 0 | 4 | 7,895 | 11.2 | answer |
| klijent-02 | POL-001 | multi-hop | DCI (wiki) | ✅ | ✅ | 1 | 11 | 12,120 | 12.0 | answer |
| klijent-03 | POL-001 | multi-hop | Agentic RAG (BM25) | ✅ | ✅ | 2 | 4 | 7,898 | 12.5 | answer |
| klijent-03 | POL-001 | multi-hop | DCI (wiki) | ✅ | ✅ | 2 | 9 | 11,617 | 12.2 | answer |
| klijent-04 | POL-001 | decline | Agentic RAG (BM25) | ❌ | ❌ | 8 | 8 | 16,556 | 12.6 | answer |
| klijent-04 | POL-001 | decline | DCI (wiki) | ❌ | ❌ | 7 | 9 | 14,636 | 13.0 | answer |
| klijent-05 | ORG-001 | multi-hop | Agentic RAG (BM25) | ✅ | ✅ | 1 | 4 | 6,945 | 11.7 | answer |
| klijent-05 | ORG-001 | multi-hop | DCI (wiki) | ✅ | ✅ | 0 | 8 | 11,662 | 12.1 | answer |
| klijent-06 | ORG-001 | multi-hop | Agentic RAG (BM25) | ✅ | ✅ | 0 | 4 | 6,990 | 10.8 | answer |
| klijent-06 | ORG-001 | multi-hop | DCI (wiki) | ✅ | ✅ | 1 | 8 | 12,336 | 15.8 | answer |
| klijent-07 | ORG-001 | multi-hop | Agentic RAG (BM25) | ✅ | ✅ | 5 | 5 | 9,316 | 15.1 | answer |
| klijent-07 | ORG-001 | multi-hop | DCI (wiki) | ✅ | ✅ | 6 | 12 | 14,138 | 17.7 | answer |
| klijent-08 | EDU-001 | multi-hop | Agentic RAG (BM25) | ✅ | ❌ | 5 | 6 | 10,924 | 15.4 | answer |
| klijent-08 | EDU-001 | multi-hop | DCI (wiki) | ✅ | ✅ | 3 | 6 | 13,128 | 12.1 | answer |
| klijent-09 | EDU-001 | multi-hop | Agentic RAG (BM25) | ❌ | ❌ | 8 | 6 | 10,717 | 13.6 | answer |
| klijent-09 | EDU-001 | multi-hop | DCI (wiki) | ✅ | ✅ | 0 | 7 | 13,201 | 8.7 | answer |
| klijent-10 | EDU-001 | decline | Agentic RAG (BM25) | ❌ | ❌ | 10 | 9 | 16,261 | 17.3 | answer |
| klijent-10 | EDU-001 | decline | DCI (wiki) | ❌ | ❌ | 0 | 16 | 18,022 | 11.7 | max_turns |
