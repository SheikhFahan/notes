---
description: Plan mode answers questions by reading. Spikes answer questions by running code.
date: 2026-10-12
---

# Spike first, plan later: using coding agents for the hard stuff  !

I was a big on planning first and then hitting the implementation pretty much all the time. Still am, for problems i know how to solve, or that someone else already has.  For hard problems that nobody has solved, spiking in auto mode until the core problem(s) is tackled gives you more speed and control around your solution.

Plan mode answers questions by reading. Spikes answer questions by running code. If the unknown is in the codebase (which files, what flow), plan. If it's in the world (does this API allow it, does this model hold accuracy on our data, is this even possible), Spike!

| Problem | Do this |
| --- | --- |
| Diff fits in one sentence | Just ask, skip the plan |
| Known answer, needs engineering | Plan mode, one-shot it |
| Nobody knows if it will work | Auto mode spikes until the core issue is resolved |

This maps to [Cynefin](https://en.wikipedia.org/wiki/Cynefin_framework): complicated problems get analysis, complex ones get small safe-to-fail experiments. Spikes themselves come from XP: the simplest program that proves you're on the right track, then thrown away ([C2 wiki](https://c2.com/xp/SpikeSolution.html)).

Agents changed two things: spikes takes an hour instead of a week, and spike code now looks shippable. Don't ship it though!

## The spike loop

1. Write the core issue as one pass/fail question.
2. Give the spike a check it can run (script, test, accuracy on 20 real samples). Auto mode's classifier blocks risky actions, not broken code.
3. Run it in auto mode on its own branch or worktree.
4. After each short burst, read what it tried and what the check said. Give feedback.
5. When it's stuck, feed it better input: open source code, error logs, GitHub issues, docs. Not a better prompt.
6. Corrected it twice on the same thing? Clear context and restart with what you learned ([Claude Code docs](https://code.claude.com/docs/en/best-practices)).
7. Wide problem space? Run a few spikes in parallel.
8. Log each result in `SPIKES.md`(your agent can do this too).

```plain
Spike, throwaway code. Question: can <X> do <Y> under <constraint>?
Only build what answers this. No UI, no error handling, no abstractions.
Check: run <script/test> and show me its output.
Refs: <docs URL>, <issue URL>, <open source repo that does this>.
Stop after 3 failed attempts and tell me what you learned.
Append the result to SPIKES.md.
```

## Then plan the real build

1. Fresh session, so dead ends don't leak in.
2. Plan mode reads `SPIKES.md`. Spike code is reference only.
3. Spike checks become the first tests.
4. Delete the spike unless you decide on purpose to keep it as a skeleton.
5. Plan hits a new unknown? Back to spikes.

## Tools worth knowing

| Tool | Use it for |
| --- | --- |
| `/goal`, Stop hooks | Keep the agent going until your check passes |
| Checkpoints, `/rewind` | Try risky things cheaply (doesn't track Bash, keep git) |
| [Simon Willison's research repo pattern](https://simonwillison.net/2025/Nov/6/async-code-research/) | A separate repo just for agent experiments |
| [Mitchell Hashimoto's harness engineering](https://mitchellh.com/writing/my-ai-adoption-journey) | Every agent mistake becomes an AGENTS.md line or a script |
| [Ralph loop](https://codecentric.de/en/knowledge-hub/blog/the-ralph-wiggum-loop-autonomous-code-generation-with-a-fresh-context) | Fresh-context loop for the build phase; set max iterations |
| [Superpowers](https://github.com/obra/superpowers), [Spec Kit](https://visualstudiomagazine.com/articles/2025/09/03/github-open-sources-kit-for-spec-driven-ai-development.aspx) | Structured plan and build after the core issue is solved |
