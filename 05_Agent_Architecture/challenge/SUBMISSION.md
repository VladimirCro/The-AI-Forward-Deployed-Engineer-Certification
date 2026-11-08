# Week 5 submission

## The room's questions

In `use_case/decisions.md`, under "Week 5 — what the room asked": two fair, one open, the rest answered.

## The second way, and why

**Second way: a skill.** Question 4 picked it: what each control asks for and what counts as evidence is knowledge the consultant owns, and it will change more often than the code. Questions 1 and 2 were no: the capability is not an existing API at work, and only my own frontend calls it. Question 3 was yes (about 4.7 searches of about 2 KB per request), but Code Mode needs a sandbox I don't have, so it stays a paragraph.

**Closest alternative I did not pick: a subagent.** The search does read a lot to return a little (about 9,300 characters for 3 or 4 documents), but it already runs as one fixed step with its own prompt, so a second model in front of it adds a call without new information.
