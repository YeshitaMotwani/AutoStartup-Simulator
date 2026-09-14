\# AutoStartup Simulator — Final Project Report



\## 1. Overview



AutoStartup Simulator is a multi-agent AI system that takes a one-line startup idea and

autonomously produces a complete startup package — market research, an MVP spec, a

live deployed landing page, a pitch deck, and a simulated adversarial investor Q\&A —

end to end, with no human in the loop. Built as a final-year resume project using

fully free-tier tooling (no paid APIs or cloud services).



\*\*Core pitch:\*\* most AI tools generate text. This orchestrates a team of specialized

agents — each with a distinct role, real tools (web search, code generation, deployment),

and the ability to fail gracefully — to produce a genuinely usable startup package

autonomously.



\## 2. Team \& Roles



| Member | Role |

|---|---|

| Yeshita | Repo owner · Orchestration (LangGraph) · CEO-agent · Investor-agent · quota/model hardening |

| Faiza | CMO-agent (market research, GTM, competitor scan) |

| Lakshit | CTO-agent (codegen + deployment) · CFO-agent (filled Sakshi's unstarted slot) · broken-main hotfix |

| Sakshi | Pitch-deck builder · Frontend (React) · frontend/backend integration |



\## 3. Architecture



```

Idea (1 line)

&#x20;  → CEO-agent (parses, delegates)

&#x20;  → CMO-agent (market research, competitors, persona, GTM)

&#x20;  → \[CTO-agent | CFO-agent] (parallel — CFO grounds its numbers in CMO's market sizing)

&#x20;  → CEO-agent (synthesizes narrative)

&#x20;  → Investor-agent (adversarial Q\&A, multi-round rebuttal, LLM-scored)

&#x20;  → Output: deployed landing page + pitch deck + Q\&A transcript + full narrative

```



\*\*Orchestration:\*\* LangGraph state machine. Topology is `parse\_idea → cmo → \[cto, cfo]`

rather than a flat 3-way fan-out, because CFO's financial estimates need CMO's TAM/SAM/SOM

as input, and the LangGraph version in use double-fires a fan-in node when incoming

branches have unequal depth — CTO is routed through CMO too, purely for scheduling

symmetry, even though its logic doesn't use CMO's output.



\*\*Resilience:\*\* every agent node is wrapped so an unhandled exception returns a safe

default instead of crashing the whole pipeline — one agent failing doesn't take down

the run.



\## 4. Tech Stack



\- \*\*Orchestration:\*\* LangGraph

\- \*\*LLM:\*\* Groq free tier — `openai/gpt-oss-120b` (quality-sensitive calls: CEO narrative,

&#x20; investor Q\&A, competitor extraction) and `openai/gpt-oss-20b` (structured/JSON calls:

&#x20; cost projections, revenue models) — migrated mid-project after Groq deprecated the

&#x20; original Llama models

\- \*\*Local fallback:\*\* Ollama, used for CMO persona generation with automatic Groq

&#x20; fallback if unreachable

\- \*\*Web search:\*\* Tavily free tier

\- \*\*Landing page generation:\*\* LLM → single-file HTML + Tailwind, with a

&#x20; generate → validate → self-correct retry loop (max 3 attempts) and a hardcoded

&#x20; fallback template if generation repeatedly fails

\- \*\*Deployment:\*\* Netlify free tier, via their file-digest deploy API (create site →

&#x20; declare file hash → upload file) — landing pages are both saved locally and deployed

&#x20; to a live public URL

\- \*\*Pitch deck:\*\* python-pptx, auto-populated 6-7 slide deck including a rendered

&#x20; screenshot of the live landing page (via Playwright)

\- \*\*Frontend:\*\* React + Vite, dark theme, live progress log, investor confidence

&#x20; score visualization

\- \*\*Backend:\*\* FastAPI



\## 5. Build Timeline (condensed)



\- \*\*Weeks 1-4:\*\* Repo scaffolding, state schema, stub pipeline wired end-to-end,

&#x20; CEO/Investor-agent skeletons, CMO-agent built out fully (Faiza)

\- \*\*Week 5-6:\*\* CTO-agent built (Lakshit) — MVP spec, tech stack recommendation,

&#x20; landing page codegen with self-correct retries. CFO-agent also built by Lakshit

&#x20; after Sakshi's slot remained unstarted. Fixed a broken `main` (a bad merge had left

&#x20; literal git conflict markers committed).

\- \*\*Week 7-9:\*\* Full pipeline running with real logic across all agents. Hardened

&#x20; against Groq's free-tier constraints: migrated models after a deprecation broke

&#x20; the pipeline overnight, fixed multiple silent-failure bugs (empty fields returned

&#x20; instead of errors under rate-limiting), added node-level fault isolation, and ran

&#x20; a 10-idea batch test with zero failures.

\- \*\*Week 8:\*\* Investor loop polish — replaced a scoring function that always returned

&#x20; 10/10 regardless of answer quality with real LLM-based scoring, expanded the question

&#x20; bank, and upgraded the rebuttal loop to allow multiple rounds per question.

\- \*\*Week 10:\*\* Real deployment (Netlify) implemented, debugged (an initial zip-upload

&#x20; approach silently served pages as plain text instead of rendering — fixed by

&#x20; switching to Netlify's file-digest API), and verified live. Full frontend built

&#x20; and wired (Sakshi): pitch deck builder, results display, live-progress UI.

&#x20; End-to-end verification completed across the whole team.



\## 6. Key Engineering Decisions \& Lessons



\- \*\*LangGraph nodes must return delta dicts, not mutated full state\*\* — a bug found

&#x20; early (parallel fan-out nodes returning the entire state object caused

&#x20; `InvalidUpdateError`) became a standing team-wide rule.

\- \*\*Mock-shadowing recurred multiple times\*\* — importing `call\_llm` (or similar)

&#x20; \*inside\* a function instead of at module top-level silently defeats `unittest.mock`

&#x20; patching in tests, causing tests to hit the real API instead of a mock. Fixed

&#x20; repeatedly across `investor\_agent.py`, `ceo\_agent.py`, `cfo\_agent.py` — worth

&#x20; flagging as a pattern to watch for in any future contribution.

\- \*\*Free-tier LLM quota is a real constraint, not a footnote\*\* — Groq's daily token

&#x20; limit was hit repeatedly during development (confirmed independently on separate

&#x20; days), sometimes mid-testing-session. This directly shaped design decisions:

&#x20; a "fast" vs "quality" model split to conserve tokens, and a documented demo-day

&#x20; contingency plan (pre-saved backup output) in case live generation fails during

&#x20; presentation.

\- \*\*Model deprecation broke the pipeline without warning\*\* — Groq removed the

&#x20; originally-used Llama models mid-project; the fix (migrating to `gpt-oss-120b/20b`)

&#x20; also incidentally increased the daily quota ceiling (100k → 200k tokens/day).

\- \*\*"Extract every X" prompts are dangerous with token budgets\*\* — an unbounded

&#x20; extraction instruction in `scan\_competitors` caused reliable JSON truncation once

&#x20; the search results were rich; the real fix was bounding the instruction ("up to 8"),

&#x20; not just raising `max\_tokens` indefinitely.

\- \*\*Netlify's raw zip-upload API doesn't reliably set Content-Type\*\* — pages deployed

&#x20; via a straightforward zip POST rendered as plain text instead of HTML in the browser.

&#x20; Switched to Netlify's file-digest flow (explicit SHA1 hash declaration + individual

&#x20; file upload), which fixed rendering.



\## 7. Known Limitations



\- \*\*Free-tier Groq quota\*\* (200k tokens/day) limits how many full pipeline runs are

&#x20; possible per day — the team mitigates this by using separate individual API accounts,

&#x20; but it remains a real constraint for extensive live demoing or stress testing.

\- \*\*`investor\_score` is LLM-judged\*\*, not a deterministic rubric — a reasonable proxy

&#x20; for pitch quality, not a precise or reproducible metric.

\- \*\*Local Ollama fallback\*\* for CMO persona generation depends on Ollama being

&#x20; installed and running on the local machine; when unavailable, the system falls

&#x20; back to Groq transparently, but this means behavior isn't fully deterministic

&#x20; across different dev machines.

\- \*\*Frontend progress streaming is time-based, not truly per-node\*\* — `GET

&#x20; /generate/stream` gives coarse progress markers rather than genuine real-time

&#x20; updates from LangGraph's execution (would require LangGraph's `astream` to do

&#x20; properly).

\- \*\*CFO/CTO share a scheduling workaround\*\* in the orchestration graph (CTO routed

&#x20; through CMO despite not using its output) due to a LangGraph version limitation —

&#x20; documented as a candidate fix if the LangGraph dependency is upgraded later.



\## 8. Final Status



All core functionality is built, tested (70+ automated tests passing), and verified

working end-to-end with real (non-mocked) API calls — including live deployment to a

real, publicly-viewable URL and a fully functional frontend. The project is

demo-ready.

