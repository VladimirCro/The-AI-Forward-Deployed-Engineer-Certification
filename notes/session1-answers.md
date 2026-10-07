# Session 1 — my answers

Answers to the questions in `01_Product_Engineering/sessions/S1_Enterprise_Dev_Environment.py`.
Kept in a separate file so the notebook stays identical to upstream.

## Question #1 — what the issuer column predicts that the status column cannot

Status only tells me the TLS handshake worked here, with this tool. The issuer
tells me whether the certificate is public or private (signed by my company),
so it predicts whether the application will work in other environments, like a
container, a server or Python's own trust store, which may not trust the
company CA.

## Question #2 — how `make check` can pass on a notebook that raises on cell three

`make check` compares the original (`.py`) and the copy (`.ipynb`) byte by byte,
but it never runs the code, so if the original has a bug, the copy has the same
bug and the check still passes. A byte-comparison gate only promises that the
two versions are consistent, not that the notebook is correct.

## Question #3 — why an approved internal gateway costs one line in `.env`

It costs one line because the code calls LiteLLM, which picks the provider from
the model string and the endpoint URL, so I only change `LLM_MODEL` and
`LLM_API_BASE` in `.env`. With a vendor SDK, the code is tied to that one
provider's client, request and response format, streaming and errors, so
switching to a provider that doesn't speak the same API means rewriting every
place the model is called. The one line covers the connection, not the
behaviour: providers still differ in supported parameters and in the output
they give, so after a switch I still have to adjust parameters and re-run the
evals.

## Question #4 — what `/clear` reveals about a rule you wrote

It tells me the rule in the file wasn't clear or specific enough to change the
agent's behaviour on its own — during the conversation the agent was following
my chat, not the file. `/clear` is a better test because it removes the
conversation and leaves only `CLAUDE.md`, the same situation as a new session
tomorrow or a colleague working on the project, so if the rule holds after
`/clear`, it holds because of the file.

In my drill, the first agent refactored an existing function I hadn't asked it
to touch. I added "Add only what was asked; don't refactor existing functions
without asking" to `challenge/CLAUDE.md`, and a fresh agent with a similar
request left the existing function alone.

## Bonus — break a gate on purpose

I added a relative link to a file that doesn't exist. `check_links.py` caught it
and printed the file, the line, the link target and the reason
(`notes/session1-answers.md:47 -> …/NE_POSTOJI.py (does not exist)`), which was
enough to fix it without guessing. Without the gate, a reviewer would have had
to click through every link in the PR to find the one that 404s.
Also noticed: on a fresh clone the gate already fails on an upstream link
(`../GLOSSARY.md`), and `make check` stops at the first failing gate, so later
gates never run until that is fixed.

## Bonus — change the provider, not the code

I changed one line in `.env` (`openai/claude-haiku-4-5` → `openai/gemini-3.5-flash`),
restarted the notebook and re-ran Task 4. A different vendor answered through the
same internal gateway, with no code changes. The answer made the same point in a
different style and with different emphasis.
What I learned on the way: `.env` is read once, so the notebook needs a restart;
a model listed by the gateway is not always usable (`gemini-3-flash-preview`
failed with a server error); and with streaming the error doesn't surface —
the reply is simply empty, so I re-ran the call without streaming to see it.
