# Week 1 submission

## Where each deliverable is

**The problem in one sentence** (`use_case/CHARTER.md`): Deciding, for every
control, which prescribed maturity level a client's evidence supports takes a
GRC consultant about four days per client, so the team cannot keep
up with organisations that must self-assess by law.

| Deliverable | Where |
| --- | --- |
| Video walkthrough (under five minutes) | https://www.loom.com/share/4fd8c77b0185438d8345b287d1761d7d |
| Charter | `use_case/CHARTER.md` |
| Schema: `Request`, `Response`, `solve()` | `01_Product_Engineering/challenge/schema.py` |
| Agent or pipeline: a pipeline, not an agent (1 of 4), with the case for an agent | `use_case/decisions.md` |
| Golden examples; which is the edge case and which the decline | `use_case/evals/golden.jsonl`; Step 7 below |
| The endpoint and the four questions | `challenge/app.py`, `challenge/frontend/index.html`; Step 8 below |
| The container, the CDN paragraph, image vs virtual environment | `challenge/Dockerfile`; Step 9 below |
| Where the app would run | Step 10 in `challenge/README.md`; `use_case/ecosystem.md`; `use_case/stakeholders.md` |
| Vibe check and the app's limitations | Step 11 in `challenge/README.md` |
| Demo to a real user | Step 12 below; `use_case/stakeholders.md`; `use_case/decisions.md` |
| Napkin math, latency, what I would swap | `## Bring it to work` in `challenge/README.md` |

## Step 7 — Golden examples

Example 3 is the edge case (two documents disagree), example 5 is the decline
(no relevant evidence, no level). Example 4 is unresolved.

## Step 8 — The endpoint

**1. What is one thing you do at work this could take over?**
Reading the client's evidence documents for one control and picking which of
the five prescribed statements they support, for documentation and for
implementation. Today a GRC consultant spends about 14 minutes per control on
this (about 4 days of reading and scoring across 137 controls per client).

**2. What exactly goes in — a string, a file, several fields?**
Two fields: a control ID from the catalog (for example `POL-001`), and a list of
evidence documents, each with an ID, a name and its text. The text is pasted in,
not uploaded as a file. The five plus five statements for the control come from
the tool's own catalog, not from the caller.

**3. What comes back, and who reads it?**
A JSON object that matches the `Response` type: a proposed level for
documentation and for implementation (or no level when the evidence is
insufficient), quotes from the documents, a short rationale, contradictions and
missing evidence. The GRC consultant reads it and makes the final decision.

**4. What did you name it, and why would an agent pick it correctly?**
`propose_control_maturity`, because the tool proposes and the consultant
decides. The verb says it only proposes, and the object says it works on one
control's maturity level.

## Step 9 — The container

**The CDN dependency.** The frontend loads the Gradio client library from a
public CDN (`cdn.jsdelivr.net`) when the page opens, and the URL does not pin a
version. On my network the corporate proxy lets that host through only with a
user login: the Windows browser gets through, but tools in WSL get a 407. The
library is fetched by the user's browser, not by the server, so running the app
in Docker does not change this. A consultant whose browser cannot reach that
CDN, for example on a stricter network, at a client site or in a locked-down
virtual desktop, would see the page load and then do nothing, with the error
only in the browser console. I would download a pinned version of the file
once, keep it in the repository and serve it from the app, so the page no
longer depends on any external host at runtime, and the build does not either.

**Image vs virtual environment.** A virtual environment holds only the Python
packages and relies on the Python, operating system and system libraries of
whatever machine it sits on. The image also carries the Python interpreter, the
operating system layer, the app code and the start command, so the platform team
can run exactly what I tested without knowing anything about Python, and only
supplies what differs per environment: the key, the internal CA and the proxy.

## Step 12 — Showing it to a real user

I showed the app to a GRC consultant: one assessment live (golden 1), then the
five golden examples and two open questions.

**1. What would you use this for?** The first pass through a client's evidence.
Today the first day or two goes on reading and finding where things are; with a
proposed level and a quote she would only check and correct it. She valued most
that it catches contradictions, such as an intranet post against board minutes,
which she can miss when reading tired, and that two consultants would give the
same evidence the same level.

**2. What is missing before you would actually use it?** Five things: drop in a
whole folder of evidence and have it sorted to the controls; change a level,
write why and keep that on record, because she signs the assessment, not the
app; export to Excel or the firm's report template; a clear answer on where the
documents go, since clients such as banks and hospitals need the data to stay in
the EU and not be used for training; and scanned PDFs with signatures, which are
about half of the evidence.

**What I see as missing:** everything the proof of concept already does and this
week's app does not: all 137 controls, a better interface, uploading and
downloading documents, and the gap analysis that comes after the assessment. On
top of that, quality and reliability checks: if we are to trust the AI, we need to
know how reliable it is.

**3. What would you expect it to cost?** She prices it against the time it saves:
a fraction of the consultant-days it removes, per analysis or as a monthly fee
per consultant. Above that it does not pay off, because she still checks
everything.

**Golden examples:** she agreed with 1, 2, 3 and 5. Example 3 was the most useful
to her: an intranet post is not evidence, board minutes are. She disagreed with
example 4: implementation 3 is generous for 58% coverage without the risk topic;
she would give 2, at most 2–3, and wants the app to show the threshold. She
settled example 6 at implementation 3, because the IT director standing in means
IT checks itself, unless the board has made a written interim appointment.

**Time:** our target is to cut reading and scoring from about 4 days to about 1
per client. Her own, more cautious estimate was about 3 days down to about 1.5;
the app does not shorten the interviews or the report.
