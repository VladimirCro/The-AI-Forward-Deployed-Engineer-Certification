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
| 2 | Project lead | Showed 20 generated rows and the datasheet. Asked what would never happen, what is missing, what would worry them if public. | Scenarios are realistic, but some levels go further than the documents allow. Missing: scans, big packages, technical evidence, evidence sent later. Worry if public: that the data looks validated when nobody checked the levels. | A consultant checks a sample of levels before Week 4. |

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
