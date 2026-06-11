# Talent-Scout — an entity-memory recruiting agent

Hand it a job description, it finds your candidates, remembers each one as an
**entity**, scores them against the JD keywords, and writes the winners to
`match.json`.

## The agent loop
```
PERCEIVE  ->  read the JD, pull out must-have + good-to-have skills
SCOUT     ->  locate candidates.csv (next to the JD, or in cwd)
REMEMBER  ->  load each candidate into ENTITY MEMORY (persisted to disk)
REASON    ->  score skills vs. required keywords, gate on must-haves
ACT       ->  write match.json + persist memory, print the verdict
```

## Run it
```bash
python recruiter_agent.py job_description.txt
```

## Files
| file                  | role                                                        |
|-----------------------|-------------------------------------------------------------|
| `job_description.txt` | input — the role you point the agent at                     |
| `candidates.csv`      | input — the talent pool the agent reads                     |
| `candidates.json`     | the same fake candidates, richer JSON form                  |
| `recruiter_agent.py`  | the agent                                                   |
| `entity_memory.json`  | **generated** — persistent memory of every entity met       |
| `match.json`          | **generated** — only the candidates who qualified           |

## How matching works
- A candidate must possess **every must-have skill** (e.g. `agentic ai`,
  `python`) — miss one and they're out.
- They also need a `match_score` (share of required keywords covered) above
  `MATCH_THRESHOLD` (default `0.30`).
- Tune `MATCH_THRESHOLD` and `SKILL_BANK` at the top of `recruiter_agent.py`.

With the sample data, only **Aarav Sharma** clears the bar. Rohan (data
scientist) is a near-miss — strong on Python/RAG/LLM but no agentic-AI signal.
Priya (frontend) doesn't match at all.

## Entity memory
`EntityMemory` stores each candidate (and the role) as an entity with
attributes + a running log of observations, persisted to `entity_memory.json`.
Run the agent twice and watch `seen_count` climb — it genuinely remembers.
This mirrors CrewAI's `EntityMemory` concept with zero external deps; swap in
CrewAI's `Crew(memory=True)` later and the same candidate-as-entity model holds.
