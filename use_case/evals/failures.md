# Failures in fifty traces

TC4 Step 1. I read fifty traces from the Week 3 endpoint (`/assess_control_for_client`), the whole flow: search, classify, assess, check the quotes. For each one I decided whether I would accept it and wrote one sentence on why not. My verdicts are in `human_scores.jsonl`.

**24 of 50 answers I would not accept. 26 I would.**

My rule: I accept an answer if a consultant could use it as a proposal, meaning the main conclusion is reasonable and it rests on the evidence of this case. A small flaw does not make an answer unusable.

## The traces

| Set | Read | Would not accept | Would accept |
| --- | ---: | ---: | ---: |
| Retrieval cases from Week 3 (`retrieval.jsonl`) | 10 | 5 | 5 |
| Goldens from Week 1 (`golden.jsonl`) | 6 | 1 | 5 |
| Synthetic rows from Week 2 (`synthetic_v2.jsonl`) | 34 | 18 | 16 |
| **Total** | **50** | **24** | **26** |

Each golden and each synthetic row was turned into a fictional client: its own documents plus about 145 noise documents from rows of the other two controls, with the same noise rules as the Week 3 clients. That way every case goes through the search, as a real request would.

## Why I would not accept them, ranked

One main reason per answer, so the counts add up to 24.

| # | Main reason | Count | Example | Component | Why it happens |
| --- | --- | ---: | --- | --- | --- |
| 1 | The search misses an important document of the case | 9 | synthetic-r400 misses the report that 145 of 150 staff completed training, then says it is not known whether training started | Search | The search is given the level scale, not a description of what the control requires, so its queries miss documents that do not use those words |
| 2 | The level has no basis in the evidence | 8 | retrieval-klijent-01 gives implementation 3 while saying itself that board adoption is not proven | Assessment prompt | The prompt has no rule that a level needs evidence for all of its conditions, so the model fills the gap with an assumption |
| 3 | It builds the answer on documents that are not evidence for this control | 7 | synthetic-r181 should decline, because the client handed in only a financial report, but scores ORG-001 from unrelated documents | Classifier | The step that labels each found document as supports, contradicts or neutral lets unrelated documents through |

In 16 of the 24 the problem is which documents reach the assessment (#1 and #3). Only 8 are about the reasoning on the level itself.

## Every failure, one sentence each

My own sentence from `human_scores.jsonl`, under its main reason.

### 1. The search misses an important document of the case (9)

- **retrieval-klijent-09:** It misses the document about the policy on the intranet and uses an unrelated roles acknowledgement to support the training assessment.
- **synthetic-r509:** It gets 2/2 but misses the supplied policy versions and supports its reasoning with unrelated records.
- **synthetic-r506:** It misses the supplied approved policy and says it is unavailable, leaving the documentation assessment incomplete.
- **synthetic-r395:** It rules out level 5 for lack of earlier training cycles even though the supplied documents include a previous cycle.
- **synthetic-r15:** It misses the explicit effectiveness assessment in r15-DOC-04 and then uses the absence of that evidence to rule out level 5.
- **synthetic-r400:** It misses the later report showing that 145 of 150 staff completed training and incorrectly declines to assess implementation.
- **synthetic-r179:** It misses the role-specific training record and creates doubts about communication using unrelated records with different employee counts.
- **synthetic-r349:** It misses the supplied approved code and gives implementation level 4 because no omissions were proven rather than because complete coverage was evidenced.
- **golden-6:** It misses the HR notice about the security lead leaving, so the assessment leaves out a key change in responsibilities.

### 2. The level has no basis in the evidence (8)

- **retrieval-klijent-01:** It gives implementation level 3 while admitting that formal adoption and the policy's required content have not been verified.
- **retrieval-klijent-05:** It treats communication to most role holders as enough for level 4 even though the location coordinator has not been informed.
- **synthetic-r249:** It says the reassignment is not formally documented even though the director has issued a written decision transferring the responsibilities.
- **synthetic-r149:** It gives documentation level 3 despite explicitly recognising that the policy has not been updated or reviewed since 2020.
- **synthetic-r12:** It infers formal adoption from partial practical use even though adoption and the required policy content have not been verified.
- **synthetic-r493:** It assigns implementation level 1 without evidence that employees are unaware of the policy and also relies on unrelated role records.
- **synthetic-r140:** It treats the earlier plan to draft a policy as proof of nonexistence without resolving the later claim that the policy is implemented.
- **synthetic-r517:** It treats missing training records and reading confirmations as proof of staff unawareness and reinforces that conclusion with an unrelated role record.

### 3. It builds the answer on documents that are not evidence for this control (7)

- **retrieval-klijent-08:** It uses unrelated signing records to create a headcount conflict and asks the client to explain a discrepancy that does not belong to this case.
- **retrieval-klijent-10:** It should decline, but gives implementation level 2 using unrelated documents about security roles.
- **synthetic-r372:** It uses an unlinked audit about another strategy to conclude that this client lacks adequate documentation and staff awareness.
- **synthetic-r181:** It should decline because the client's financial report says nothing about security roles, but it scores using unrelated documents.
- **synthetic-r505:** It uses an unrelated approval of policy version 2.2 to make this client's documentation appear updated.
- **synthetic-r180:** It should decline because the infrastructure plan does not evidence security roles, but it assigns levels from unrelated documents.
- **synthetic-r77:** It gives a single 3/3 assessment before establishing which company the documents belong to.
## Smaller issues in answers I would accept

These did not change my verdict, but they are real and worth fixing:

- A contradiction that is not one, such as "planned for April" and "held in April", or a wider job description against a short summary (synthetic-r252, r311, r339, r64).
- Doubt that is written in the rationale but not flagged as low confidence (retrieval-klijent-06, synthetic-r484).
- Asking for evidence the client already handed in (synthetic-r95).
- A decline that does not say what to ask the client for: retrieval-klijent-04 asks only for "documents that prove this control". Added after the consultant's review on 2 Nov; she wants the policy and the proof of its adoption named.

A stricter first read, which counted every imperfection like these, found something in 39 of 50 traces. The main count above uses my acceptance rule instead.

## How consistent I was

I scored the same cases in two rounds, a first set of twenty and then all fifty. On the fifteen cases that were in both rounds and ran on the same version, my verdicts agree fifteen times out of fifteen.

One rule became explicit along the way. retrieval-klijent-01 and synthetic-r12 give implementation 3 although board adoption is not proven, and I did not accept them. synthetic-r36 also gives 3, but there the adoption decision is in the documents, and I accepted it. So: level 3 for a policy needs proof of adoption, not only signs that it is used.

## Limits of this read

- For synthetic rows the expected level is noisy: in Week 2, 313 of 548 rows did not match their recipe. I judged each answer against the documents, not only against Expected.
- Noise documents come from different fictional companies, so their figures can disagree (89 vs 120 employees). A real client's documents would not disagree like that.
- The Week 2 documents are short, each row covers one control, and no document serves several controls, so the search here is easier than on a real client.
- Goldens 4 and 6 have unresolved levels (see `golden.jsonl`). Golden-6 is not accepted because the search missed one of its documents, not because of the level.

## What the failures point to

Most failures start before the assessment: the search misses documents (#1) and the classifier lets unrelated ones in (#3). When the right documents arrive, the levels are mostly right: five of six goldens are accepted. The next change is the search and classification flow, then the prompt rule behind #2.
