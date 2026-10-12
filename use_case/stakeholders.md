# Stakeholders

Everyone you talk to about this project, from the first "where would this even
run?" to the final readout.

> **Week 10's technical challenge is a client report to the people in this file.**
> You cannot write it later from memory. Add a row the day you have the
> conversation.

Use roles, not names. This is a public fork.

| Week | Who (role) | What you asked | What you learned | Follow-up |
| --- | --- | --- | --- | --- |
| 1 | Platform team lead (owns the shared Kubernetes clusters) | Where does an internal container app run and how does it get there? (confirmed during my three earlier deploys) | Shared GKE clusters, internal registry, Entra ID, egress through NAT and allowlist, approved model access through Vertex AI or the internal gateway | Confirm the Vertex AI or gateway choice when this app is deployed |
| 1 | GRC consultant (the user from the charter) | How long does a full engagement take, how many consultants are there, how much demand is waiting? | About 7 consultant-days for the assessment plus the gap report; six consultants; more clients in the pipeline than the team can start; a separate, larger market for plain legal compliance | Book a 30-minute demo of the app before the deadline |

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
