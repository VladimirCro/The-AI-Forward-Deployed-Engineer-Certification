# TC1 Build questions — my answers

The eight questions from the Build table in `01_Product_Engineering/challenge/README.md`:
1–4 are asked in the Session 1 notebook, 5–8 in the Session 2 discussion.
Kept in a separate file so the notebook stays identical to upstream.

## Question 1 — Session 1

> The probe reports the **certificate issuer** for each host, not just whether the host was reachable. A colleague argues the issuer column is noise — everything connected, so the network is fine. In one to three sentences, explain what the issuer column predicts that the status column cannot.

**Answer:**

Status only tells me the TLS handshake worked here, with this tool. The issuer
tells me whether the certificate is public or private (signed by my company),
so it predicts whether the application will work in other environments, like a
container, a server or Python's own trust store, which may not trust the
company CA.

## Question 2 — Session 1

> `make check` passes on a notebook that raises an exception on its third cell. Explain how both of those can be true at once, and what that tells you about what a byte-comparison gate is actually able to promise.

**Answer:**

`make check` compares the original (`.py`) and the copy (`.ipynb`) byte by byte,
but it never runs the code, so if the original has a bug, the copy has the same
bug and the check still passes. A byte-comparison gate only promises that the
two versions are consistent, not that the notebook is correct.

## Question 3 — Session 1

> Your egress probe shows no route to a hosted provider, but an approved internal gateway is reachable. Explain, in one to three sentences, why that costs one line in `.env` here — and what specifically you would have had to rewrite if the code had called a vendor SDK directly.

**Answer:**

It costs one line because the code calls LiteLLM, which picks the provider from
the model string and the endpoint URL, so I only change `LLM_MODEL` and
`LLM_API_BASE` in `.env`. With a vendor SDK, the code is tied to that one
provider's client, request and response format, streaming and errors, so
switching to a provider that doesn't speak the same API means rewriting every
place the model is called. The one line covers the connection, not the
behaviour: providers still differ in supported parameters and in the output
they give, so after a switch I still have to adjust parameters and re-run the
evals.

## Question 4 — Session 1

> You add a rule to `CLAUDE.md`, and the agent follows it for the rest of that conversation. After `/clear`, it goes back to the old behaviour. What does that specific outcome tell you about the rule you wrote — and why is `/clear` a better test than simply continuing the conversation?

**Answer:**

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

## Question 5 — Session 2 discussion

> What breaks when a low-confidence answer and *no answer* share one field.

**Answer:**

If "not sure" and "no answer" share one field, a missing answer gets written as
a number and reads like a real assessment, and nobody can tell "check this
proposal" apart from "ask the client for documents". For my project that means a
control with no evidence could show up as level 1 in an audit report, and the
evals could not measure how often the system correctly declined. So my
`Response` keeps them separate: `level` is empty when there is no evidence, with
the reason "insufficient evidence", and a separate flag marks a low-confidence
proposal for the consultant to review.

## Question 6 — Session 2 discussion

> Why a token bill that scales with steps is harder to defend than one that scales with requests.

**Answer:**

A bill that scales with requests is predictable: the same number of model calls
per request, so the cost per assessment can be quoted up front. A bill that
scales with steps depends on how many steps an agent decides to take, so the same
request can cost a little or a lot, one bad case can loop and burn tokens, and it
is hard to explain to whoever pays. For my project the core proposal is a fixed
pipeline with a predictable cost per control; only the evidence search would be
agentic, so I would cap its steps per control to keep the bill defensible.
Capping steps trades cost for recall, so when the agent hits the cap it should
decline ("insufficient evidence found") rather than guess, and the cap itself
should be chosen by measuring recall and cost on the golden examples, not picked
up front.

## Question 7 — Session 2 discussion

> Why scoring against a model-generated example reports success for a system that is uniformly wrong.

**Answer:**

If the "correct" answer was written by a model, it shares the same blind spots as
the system being tested, so when both are wrong in the same way the eval only
measures that they agree, not that they are right, and a uniformly wrong system
scores 100%. For my project a model might rate an unadopted draft policy as
level 3; if the golden example says 3 too, the eval passes, while a consultant
would say 2. That is why my golden examples are written by hand from the
calculator's rules and a consultant's judgement, not generated.

## Question 8 — Session 2 discussion

> Whether cost or latency is more likely to stop your application being used.

**Answer:**

Latency, not cost. The model costs cents per control, which is negligible next
to a consultant's hourly rate, as long as the agentic search has a step cap. But
if each control takes a minute or two and the consultant has to sit and wait,
137 controls become hours of waiting and they will go back to the spreadsheet.
So I would run all controls for a client in the background and let the
consultant review finished proposals, rather than make them wait on each one.
(Both numbers are estimates for now; they get measured in TC1 Step 13.)

## Bonus — break a gate on purpose

I added a relative link to a file that doesn't exist. `check_links.py` caught it
and printed the file, the line, the link target and the reason
(`notes/<this file>:47 -> …/NE_POSTOJI.py (does not exist)`), which was
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
