# The ecosystem you deploy into

Where your application would actually run, inside your actual firm.

> **Week 1 starts this file. Week 9 finishes it.**
> TC1 Step 10 asks eight questions. The full Week 9 checklist has around thirty,
> and the eight are a strict subset — so nothing here gets thrown away.

Describe patterns, not specifics. "On-prem OpenShift, images from an internal
registry, no public egress" is useful to everyone and identifies nobody. Never
put real hostnames, IPs, or architecture diagrams in this file.

---

## Week 1 — the first eight questions

<!-- Answered in TC1 Step 10. Bring these back from a real conversation. -->

**Who did you ask?** (role, not name)

The platform team lead who owns the shared clusters. From my own experience
deploying three apps on this platform, confirmed with the platform team lead
during each deploy.

| # | Question | Answer |
| :---: | --- | --- |
| 1 | Where do internal apps run? (k8s, ECS, App Service, a VM someone maintains) | Shared, firm-managed GKE clusters; each app is a guest in its own namespace. Separate dev and prod clusters. Internal-only, behind an internal HTTPS gateway, reached from the internal network or VPN. |
| 2 | Which cloud? AWS, Azure, GCP, on-prem, several? | GCP, attached to the firm's network through a shared VPC. |
| 3 | Is there an internal container registry? | Yes: a shared Artifact Registry for dev and prod, versions told apart by tag. Images are built by Cloud Build from CI. A shared Helm chart is published there too. |
| 4 | How do users log in? (Okta, Entra ID, Ping, SAML, homegrown) | Entra ID (single sign-on); roles are checked in the backend. External partners come in as guest users. |
| 5 | Can the app reach the internet? Egress proxy? Allowlist? | Not freely. Egress goes through Cloud NAT with a fixed address that specific external services allowlist. No public LLM API is needed. |
| 6 | Where do secrets come from? (Vault, Secrets Manager, Key Vault) | Masked CI variables, written into Kubernetes secrets at deploy time. Access to GCP services uses workload identity, so no keys. Secret Manager is available. |
| 7 | Who approves a deployment, and what review does it need? | Dev deploys automatically from CI. Prod never deploys on its own: one manual approval by the app owner, then the pipeline runs. Cluster-side changes (routing, TLS, NAT) go through the platform team. |
| 8 | Is there an approved internal LLM endpoint already? | Yes, two: the internal LLM gateway this app uses today, and Vertex AI inside our own GCP project (EU region), which our existing products use directly. |

**What surprised you?**

Nothing surprised me: I have already deployed three apps on this platform.

**What would you have to change about your app to deploy there?**

Entra ID login; CI build and push to the internal registry; the shared Helm chart;
secrets from CI or workload identity instead of `--env-file`; no public CDN at
runtime; internal CA in the trust store; possibly Vertex AI instead of the gateway.

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

### 2026-10-07 — the same hosts through the corporate proxy

| host | tunnel via proxy | server reply | certificate issuer |
| --- | --- | --- | --- |
| pypi.org | 200 | 200 | GlobalSign (public) |
| files.pythonhosted.org | 200 | 404 on `/` (host reachable) | GlobalSign (public) |
| api.openai.com | 200 | 421 on `/` (host reachable) | Google Trust Services (public) |
| cdn.jsdelivr.net | **407 — proxy requires authentication** | — | — |
| huggingface.co | 200 | 200 | Amazon (public) |
| registry-1.docker.io | 200 | 404 on `/` (host reachable) | Amazon (public) |
| github.com | 200 | 200 | Sectigo (public) |

**How measured:** `curl -sv https://<host>/` from the same laptop, through the
proxy already configured in the shell (`https_proxy`). Read three lines from
the verbose output: the proxy's reply to `CONNECT` (tunnel), the server's HTTP
status, and the certificate `issuer`. Compared with the notebook probe, which
connects directly and bypasses the proxy.

**Reading:** an allowlist behind an authenticating proxy, with no TLS interception.
Every certificate is from a public CA. Six of seven hosts tunnel without a login;
the frontend's CDN only passes with a proxy login, which a browser on the
corporate laptop sends automatically and tools in WSL do not.

**What it predicts:** open weights from huggingface.co (Weeks 2 and 8) and
container base images from Docker Hub (Week 9) are reachable through the proxy.
The CDN is the risk: the client library is fetched by each user's browser, not
by the server, so the Week 1 frontend works for anyone whose browser gets
through the proxy and silently does nothing for anyone whose browser does not.
The client library should be vendored.
Anything calling an internal service needs the internal CA, which tools inside a
container will not trust by default.

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
  in the Windows browser. The browser fetches it, not the server, so the app
  works for users whose browser gets through and breaks for users whose browser
  does not, wherever the app itself runs.
- On 2026-10-07 the proxy failed to resolve Google API domains
  (502 notresolvable) while other domains worked — a temporary proxy-side DNS
  issue, not a local one.

### 2026-10-11 — what building and running the container showed

- **`ghcr.io` needs a proxy login (407).** The course Dockerfile pulled `uv` from
  there, so the build failed. `uv` now comes from PyPI, which the proxy lets
  through, pinned to one version.
- **`docker build` does not inherit the shell's proxy.** Package installs inside
  the build need the proxy passed in as build arguments; those are not stored in
  the image.
- **The container does not trust the internal CA.** Calling the internal LLM
  gateway failed with `CERTIFICATE_VERIFY_FAILED`. Mounting the host's CA bundle
  read-only at run time and pointing `SSL_CERT_FILE` at it fixed it, with no
  certificate in the image or the repo. This is not TLS interception: public
  hosts still show public certificates; the gateway is an internal server.

### 2026-10-18, Week 2: downloading open weights

- **The model page loads, the weights do not.** `huggingface.co` answers through the proxy, but the weights come from a CDN (`*.cdn.hf.co`, `*.xethub.hf.co`) that the proxy refuses (407). The Week 1 prediction above was wrong: reaching the page is not the same as downloading the model.
- **The PyTorch package index is refused too (407).** torch came from PyPI instead, as a much larger GPU build.
- **How I got the model for Session 3:** I downloaded it once outside the firm network (phone hotspot, no VPN, no proxy) into the local cache; after that it loads from disk.
- **For Weeks 8 and 9:** an allowlist entry for those hosts, or an internal model registry, is needed before an open-weights model can run on the firm's machines.

---

## Week 9 — the full checklist

<!--
  TC9 extends this same file. Do not start a new one: the point is that the git
  history shows one continuous piece of work from Week 1 to Week 9.
-->

<!-- Week 9 -->
