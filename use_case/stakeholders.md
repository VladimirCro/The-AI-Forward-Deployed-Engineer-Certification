# Stakeholders

Everyone you talk to about this project, from the first "where would this even
run?" to the final readout.

> **Week 10's technical challenge is a report to the people in this file.**
> You cannot write it later from memory. Add a row the day you have the
> conversation.

Use roles, not names. This is a public repo.

| Week | Who (role) | What you asked | What you learned | Follow-up |
| --- | --- | --- | --- | --- |
| 1 | Platform team lead (owns the shared Kubernetes clusters) | Where does an internal container app run and how does it get there? (confirmed during my three earlier deploys) | Shared GKE clusters, internal registry, Entra ID, egress through NAT and allowlist, approved model access through Vertex AI or the internal gateway | Confirm the Vertex AI or gateway choice when this app is deployed |
| 1 | GRC consultant (the user from the charter) | How long does a full engagement take, how many consultants are there, how much demand is waiting? | About 7 consultant-days for the assessment plus the gap report; six consultants; more clients in the pipeline than the team can start; a separate, larger market for plain legal compliance | Show her this app and the five golden examples; ask what is missing and what it should cost |
| 1 | GRC consultant (demo of this app) | What would you use it for, what is missing, what should it cost? Do you agree with the five examples? | First pass through the evidence; contradictions are the most valuable part; needs folder upload, recorded overrides, export, EU data residency and OCR; agreed with four examples, not with golden 4 | Agree the coverage threshold for level 3; show which scale statement was applied |
| 2 | Project lead | Showed 20 generated rows and the datasheet. Asked what would never happen, what is missing, what would worry them if public. | Scenarios are realistic, but some levels go further than the documents allow. Missing: scans, big packages, technical evidence, evidence sent later. Worry if public: that someone takes the generated levels as an expert's answers. They look finished, but the model wrote them and no consultant has confirmed them. | A consultant checks a sample of levels before they are used to score or train anything. |
| 3 | GRC consultant (the problem owner) | Eight cases run through the client endpoint (chosen by me; synthetic clients): would you act on this answer, does the source convince you, what did you want to ask? | She would accept five of eight. For a document from another topic (the rulebook r179-DOC-01 in klijent-01) she would first confirm it belongs to the case. She wanted to ask the tool "which evidence is this based on, and what would change the level?" | Four cases into `retrieval.jsonl` after the TC4 baseline; tell "not found" apart from "not provided" in the next search change. |
| 4 | GRC consultant | A written five-minute demo (problem, numbers, one failure, next steps) and three questions: what would you do differently on Monday, what would convince you the number is wrong, what did you expect to see? | She would run a limited pilot with mandatory consultant review and measure the time really saved, including review and corrections. What would show her the numbers are wrong: an independent review of all 50 answers against rules agreed in advance that gives different results, with the exact version of every answer kept. She wanted to see the assessment date, the original document one click away, and a view of which condition of the level is confirmed and which is not. From eight examples she would not yet confirm that most failures are in the search; for that she wants the findings for all 50 grouped. She confirmed two rules: a missing record alone does not give level 1, and a level with an open check is fine only if the check does not decide the level. On the five cases where the 2 Nov answer had the same levels as the one I read on 1 Nov, her verdict matched mine four times. | Send her `failures.md` with all 50 grouped; write the decision rules with her; plan how the pilot measures time; a two-hour session with her on 5 Nov. |

---

## Not everyone is an infrastructure contact

The useful list is wider than it first looks, and Week 10's report goes to all of
them:

- **The person with the problem** — the one from your charter. Have you shown
  them anything yet?
- **Whoever owns the data** you would need.
- **Whoever runs the platform** your app would deploy onto.
- **Whoever approves** a deployment, a spend, or a vendor.
- **Your own manager**, who will be asked whether this was worth the ten weeks.

If a week goes by with no conversation, add a row saying so and why. A visible
gap is more useful than a silent one.
