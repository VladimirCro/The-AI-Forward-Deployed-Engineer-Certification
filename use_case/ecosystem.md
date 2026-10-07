# Someone else's ecosystem

Where your application would actually run, inside your actual firm.

> **Week 1 starts this file. Week 9 finishes it.**
> TC1 Step 6 asks eight questions. The full Week 9 checklist has around thirty,
> and the eight are a strict subset — so nothing here gets thrown away.

Describe patterns, not specifics. "On-prem OpenShift, images from an internal
registry, no public egress" is useful to everyone and identifies nobody. Never
put real hostnames, IPs, or architecture diagrams in this file.

---

## Week 1 — the first eight questions

<!-- Answered in TC1 Step 6. Bring these back from a real conversation. -->

**Who did you ask?** (role, not name)

<!-- your answer here -->

| # | Question | Answer |
| :---: | --- | --- |
| 1 | Where do internal apps run? (k8s, ECS, App Service, a VM someone maintains) | <!-- --> |
| 2 | Which cloud? AWS, Azure, GCP, on-prem, several? | <!-- --> |
| 3 | Is there an internal container registry? | <!-- --> |
| 4 | How do users log in? (Okta, Entra ID, Ping, SAML, homegrown) | <!-- --> |
| 5 | Can the app reach the internet? Egress proxy? Allowlist? | <!-- --> |
| 6 | Where do secrets come from? (Vault, Secrets Manager, Key Vault) | <!-- --> |
| 7 | Who approves a deployment, and what review does it need? | <!-- --> |
| 8 | Is there an approved internal LLM endpoint already? | <!-- --> |

**What surprised you?**

<!-- your answer here -->

**What would you have to change about your app to deploy there?**

<!-- your answer here -->

---

## Week 1 — what your machine told you

<!--
  Paste the egress probe output from Session 1 here. It is evidence, and it
  frequently disagrees with what people believe about their own network.
-->

### 2026-10-07 — Session 1 egress probe (developer laptop, WSL2)

| host | why | status | underlying error |
| --- | --- | --- | --- |
| pypi.org | Python packages | DNS BLOCKED | no answer within the probe's deadline |
| files.pythonhosted.org | the actual wheel downloads | DNS BLOCKED | no answer within the probe's deadline |
| api.openai.com | the model API | TLS BLOCKED | network is unreachable |
| cdn.jsdelivr.net | the CDN the Week 1 frontend uses | TLS BLOCKED | network is unreachable |
| huggingface.co | open weights, Weeks 2 and 8 | DNS BLOCKED | no answer within the probe's deadline |
| registry-1.docker.io | container images | DNS BLOCKED | no answer within the probe's deadline |
| github.com | this repository | TLS BLOCKED | connection timed out |

**Verdict (probe):** Blocked: pypi.org, files.pythonhosted.org, api.openai.com, cdn.jsdelivr.net, huggingface.co, registry-1.docker.io, github.com. Someone has to allow these or mirror them internally before Weeks 2, 8, and 9 — find out who, now, not in the week you need it.

**Does this match what you were told in the table above?** Where it doesn't, that
gap is worth chasing — it usually means a proxy nobody documented.

Only partly. The probe connects directly and ignores the proxy, so it reports
everything as blocked: this laptop has no direct egress at all. None of the
failures is a certificate problem — the connection never gets that far. Through
the corporate proxy most hosts work (pypi.org, github.com and huggingface.co
return 200), so the real constraint is "proxy only, allowlisted", not
"everything blocked". DNS vs TLS BLOCKED is incidental here; the finding is the
same for every host.

Two more things the probe cannot see:
- The CDN the frontend loads is refused by the proxy from WSL (407) but loads
  in the Windows browser, so the chat works locally but would likely break on a
  server without a user's proxy login.
- On 2026-10-07 the proxy failed to resolve Google API domains
  (502 notresolvable) while other domains worked — a temporary proxy-side DNS
  issue, not a local one.

---

## Week 9 — the full checklist

<!--
  TC9 extends this same file. Do not start a new one: the point is that the git
  history shows one continuous piece of work from Week 1 to Week 9.
-->

<!-- Week 9 -->
