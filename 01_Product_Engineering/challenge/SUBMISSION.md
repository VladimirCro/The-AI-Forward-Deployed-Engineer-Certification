# Week 1 submission

## Step 7 — Golden examples

Example 3 is the edge case (two documents disagree), example 5 is the decline
(no relevant evidence, no level). Example 6 is unresolved.

## Step 8 — The endpoint

**1. What is one thing you do at work this could take over?**
Reading the client's evidence documents for one control and picking which of
the five prescribed statements they support, for documentation and for
implementation. Today a GRC consultant spends about 14 minutes per control on
this, across 137 controls per client.

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
