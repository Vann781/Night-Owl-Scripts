"""
================================================================
  TALENT-SCOUT  ::  an entity-memory recruiting agent
================================================================

What it does
------------
You hand it a Job Description file. It hunts down `candidates.csv`
sitting next to that file, loads every candidate into its ENTITY
MEMORY (each candidate becomes a remembered "entity"), figures out
which skills the JD actually demands, reasons over memory to score
each candidate, and writes the winners to `match.json`.

The agent loop:  PERCEIVE -> REMEMBER -> REASON -> ACT

Run it:
    python recruiter_agent.py path/to/job_description.txt

Files it touches:
    reads   : <jd>            (the job description you point it at)
    reads   : candidates.csv  (found next to the JD, or in cwd)
    writes  : entity_memory.json  (persistent memory of candidates)
    writes  : match.json          (the qualified candidates)
"""

import csv
import json
import os
import re
import sys
import time
from datetime import datetime, timezone

# --------------------------------------------------------------------------
#  a little color, so the agent feels alive in the terminal
# --------------------------------------------------------------------------
_USE_COLOR = sys.stdout.isatty() and os.environ.get("NO_COLOR") is None


def c(text, code):
    if not _USE_COLOR:
        return text
    return f"\033[{code}m{text}\033[0m"


def dim(t):    return c(t, "2")
def bold(t):   return c(t, "1")
def green(t):  return c(t, "92")
def red(t):    return c(t, "91")
def yellow(t): return c(t, "93")
def cyan(t):   return c(t, "96")
def magenta(t):return c(t, "95")


def banner():
    art = r"""
  ╔══════════════════════════════════════════════════╗
  ║   T A L E N T - S C O U T   ·   entity-memory ai   ║
  ╚══════════════════════════════════════════════════╝
"""
    print(magenta(art))


def phase(label, detail=""):
    print(f"{cyan('▸')} {bold(label)} {dim(detail)}")


def think(msg):
    # tiny "the agent is reasoning" effect
    print(f"   {dim('· ' + msg)}")
    if _USE_COLOR:
        time.sleep(0.15)


# --------------------------------------------------------------------------
#  ENTITY MEMORY
#  A persistent store of "entities" the agent has met. Here every
#  candidate is an entity with a type, attributes and observations.
#  Mirrors the idea behind CrewAI's EntityMemory, but with zero deps.
# --------------------------------------------------------------------------
class EntityMemory:
    def __init__(self, path):
        self.path = path
        self.entities = {}
        self._load()

    def _load(self):
        if os.path.exists(self.path):
            try:
                with open(self.path, "r", encoding="utf-8") as f:
                    self.entities = json.load(f).get("entities", {})
            except (json.JSONDecodeError, OSError):
                self.entities = {}

    def remember(self, key, etype, attributes, observation=None):
        """Store or update an entity in memory."""
        now = datetime.now(timezone.utc).isoformat()
        if key in self.entities:
            ent = self.entities[key]
            ent["attributes"].update(attributes)
            ent["last_seen"] = now
            ent["seen_count"] = ent.get("seen_count", 1) + 1
        else:
            ent = {
                "type": etype,
                "attributes": attributes,
                "observations": [],
                "first_seen": now,
                "last_seen": now,
                "seen_count": 1,
            }
            self.entities[key] = ent
        if observation:
            ent["observations"].append({"at": now, "note": observation})
        return ent

    def recall(self, key):
        return self.entities.get(key)

    def of_type(self, etype):
        return {k: v for k, v in self.entities.items() if v["type"] == etype}

    def save(self):
        payload = {
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "entity_count": len(self.entities),
            "entities": self.entities,
        }
        with open(self.path, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2, ensure_ascii=False)


# --------------------------------------------------------------------------
#  SKILL BANK
#  Canonical skills + the aliases the agent recognizes in free text.
# --------------------------------------------------------------------------
SKILL_BANK = {
    "agentic ai":       ["agentic ai", "ai agent", "ai agents", "autonomous agent",
                         "autonomous agents", "multi-agent", "agent framework"],
    "python":           ["python"],
    "langchain":        ["langchain"],
    "langgraph":        ["langgraph"],
    "crewai":           ["crewai", "crew ai"],
    "rag":              ["rag", "retrieval augmented", "retrieval-augmented"],
    "llm":              ["llm", "llms", "large language model", "gpt", "claude"],
    "vector database":  ["vector database", "vector db", "pinecone", "chroma",
                         "weaviate", "faiss"],
    "docker":           ["docker", "container"],
    "kubernetes":       ["kubernetes", "k8s"],
    "aws":              ["aws", "amazon web services"],
    "ci/cd":            ["ci/cd", "cicd", "ci cd", "continuous integration"],
    "java":             ["java"],
    "flutter":          ["flutter"],
    "html":             ["html"],
    "css":              ["css"],
    "javascript":       ["javascript", " js ", "js,"],
    "react":            ["react"],
    "machine learning": ["machine learning", " ml ", "ml,"],
    "tensorflow":       ["tensorflow"],
    "sql":              ["sql"],
    "pandas":           ["pandas"],
}


def canonicalize(raw_skill):
    """Map a raw skill string to a canonical skill name (or itself)."""
    s = raw_skill.strip().lower()
    for canon, aliases in SKILL_BANK.items():
        if s == canon or s in aliases:
            return canon
    return s  # unknown skill -> keep as-is, lowercased


def scan_text_for_skills(text):
    """Find every canonical skill mentioned anywhere in a block of text."""
    t = " " + text.lower() + " "
    found = set()
    for canon, aliases in SKILL_BANK.items():
        for needle in [canon] + aliases:
            if needle in t:
                found.add(canon)
                break
    return found


# --------------------------------------------------------------------------
#  JOB DESCRIPTION parsing
# --------------------------------------------------------------------------
def parse_jd(path):
    with open(path, "r", encoding="utf-8") as f:
        text = f.read()

    title = ""
    m = re.search(r"job title\s*:\s*(.+)", text, re.IGNORECASE)
    if m:
        title = m.group(1).strip()

    def grab(label):
        m = re.search(rf"{label}\s*:\s*(.+)", text, re.IGNORECASE)
        if not m:
            return set()
        return {canonicalize(x) for x in re.split(r"[;,]", m.group(1)) if x.strip()}

    must_have = grab("must-have skills") or grab("must have skills")
    good_to_have = grab("good-to-have skills") or grab("good to have skills")

    # Anything else the JD mentions counts as "required context"
    mentioned = scan_text_for_skills(text)

    # If the JD declared nothing explicit, fall back to title + body scan.
    if not must_have:
        title_skills = scan_text_for_skills(title)
        must_have = title_skills or {next(iter(mentioned), "")} - {""}

    required = (must_have | good_to_have | mentioned)
    required.discard("")
    return {
        "title": title or os.path.basename(path),
        "must_have": must_have,
        "good_to_have": good_to_have,
        "required": required,
        "raw": text,
    }


# --------------------------------------------------------------------------
#  the AGENT
# --------------------------------------------------------------------------
class RecruiterAgent:
    MATCH_THRESHOLD = 0.30  # fraction of required skills a candidate must cover

    def __init__(self, workdir):
        self.workdir = workdir
        self.memory = EntityMemory(os.path.join(workdir, "entity_memory.json"))

    # ---- PERCEIVE -------------------------------------------------------
    def perceive_jd(self, jd_path):
        phase("PERCEIVE", "reading the job description")
        jd = parse_jd(jd_path)
        think(f"role detected: {jd['title']}")
        think(f"must-have skills: {', '.join(sorted(jd['must_have'])) or '(none stated)'}")
        think(f"good-to-have: {', '.join(sorted(jd['good_to_have'])) or '(none stated)'}")
        # remember the role itself as an entity too
        self.memory.remember(
            key=f"role::{jd['title']}",
            etype="role",
            attributes={
                "title": jd["title"],
                "must_have": sorted(jd["must_have"]),
                "good_to_have": sorted(jd["good_to_have"]),
                "required": sorted(jd["required"]),
            },
            observation="Opened a search for this role.",
        )
        return jd

    def find_candidates_file(self, jd_path):
        phase("SCOUT", "looking for candidates.csv")
        candidates_paths = [
            os.path.join(os.path.dirname(os.path.abspath(jd_path)), "candidates.csv"),
            os.path.join(self.workdir, "candidates.csv"),
            os.path.join(os.getcwd(), "candidates.csv"),
        ]
        for p in candidates_paths:
            if os.path.exists(p):
                think(f"found it -> {p}")
                return p
        raise FileNotFoundError("Could not find candidates.csv near the JD or in cwd.")

    # ---- REMEMBER -------------------------------------------------------
    def remember_candidates(self, csv_path):
        phase("REMEMBER", "loading candidates into entity memory")
        rows = []
        with open(csv_path, newline="", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                raw_skills = [s for s in re.split(r"[;,]", row.get("skills", "")) if s.strip()]
                canon_skills = sorted({canonicalize(s) for s in raw_skills})
                self.memory.remember(
                    key=f"candidate::{row['id']}",
                    etype="candidate",
                    attributes={
                        "id": row["id"],
                        "name": row["name"],
                        "email": row.get("email", ""),
                        "current_role": row.get("current_role", ""),
                        "experience_years": row.get("experience_years", ""),
                        "location": row.get("location", ""),
                        "skills_raw": raw_skills,
                        "skills": canon_skills,
                    },
                    observation="Indexed candidate skills.",
                )
                think(f"remembered {row['name']} ({len(canon_skills)} skills)")
                rows.append(row["id"])
        return rows

    # ---- REASON ---------------------------------------------------------
    def evaluate(self, jd):
        phase("REASON", "scoring candidates against the role")
        required = jd["required"]
        must_have = jd["must_have"]
        results = []

        for key, ent in self.memory.of_type("candidate").items():
            attrs = ent["attributes"]
            skills = set(attrs["skills"])

            matched_required = sorted(skills & required)
            missing_must = sorted(must_have - skills)
            score = (len(skills & required) / len(required)) if required else 0.0

            has_all_must = len(missing_must) == 0
            qualifies = has_all_must and score >= self.MATCH_THRESHOLD

            verdict = (
                "MATCH" if qualifies
                else ("MISSING MUST-HAVE" if not has_all_must else "BELOW THRESHOLD")
            )

            # write the verdict back into memory as an observation
            self.memory.remember(
                key=key, etype="candidate", attributes={},
                observation=f"Evaluated for '{jd['title']}': {verdict} "
                            f"(score {score:.0%}).",
            )

            results.append({
                "id": attrs["id"],
                "name": attrs["name"],
                "email": attrs["email"],
                "current_role": attrs["current_role"],
                "experience_years": attrs["experience_years"],
                "location": attrs["location"],
                "skills": attrs["skills"],
                "matched_keywords": matched_required,
                "missing_must_have": missing_must,
                "match_score": round(score, 2),
                "qualifies": qualifies,
                "verdict": verdict,
            })

        results.sort(key=lambda r: (r["qualifies"], r["match_score"]), reverse=True)
        return results

    # ---- ACT ------------------------------------------------------------
    def report_and_save(self, jd, results):
        phase("ACT", "deciding and writing match.json")
        print()
        print("   " + bold(f"Role: {jd['title']}"))
        print("   " + dim("required keywords: " + ", ".join(sorted(jd["required"]))))
        print()

        for r in results:
            mark = green("✓ MATCH ") if r["qualifies"] else red("✗ " + r["verdict"])
            print(f"   {mark}  {bold(r['name'])}  "
                  f"{dim('· score ' + format(r['match_score'], '.0%'))}")
            print(f"        {dim('matched :')} "
                  f"{green(', '.join(r['matched_keywords']) or '—')}")
            if r["missing_must_have"]:
                print(f"        {dim('missing :')} "
                      f"{red(', '.join(r['missing_must_have']))}")
        print()

        matched = [r for r in results if r["qualifies"]]
        out = {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "role": jd["title"],
            "required_keywords": sorted(jd["required"]),
            "must_have": sorted(jd["must_have"]),
            "matched_count": len(matched),
            "candidates": matched,
        }
        match_path = os.path.join(self.workdir, "match.json")
        with open(match_path, "w", encoding="utf-8") as f:
            json.dump(out, f, indent=2, ensure_ascii=False)

        self.memory.save()

        if matched:
            names = ", ".join(m["name"] for m in matched)
            print("   " + green(bold(f"MATCH SUCCESS — {len(matched)} candidate(s): {names}")))
        else:
            print("   " + yellow(bold("No candidate cleared the bar for this role.")))
        print("   " + dim(f"-> wrote {match_path}"))
        print("   " + dim(f"-> memory persisted to {self.memory.path}"))
        print()
        return match_path

    # ---- run the full loop ---------------------------------------------
    def run(self, jd_path):
        jd = self.perceive_jd(jd_path)
        csv_path = self.find_candidates_file(jd_path)
        self.remember_candidates(csv_path)
        results = self.evaluate(jd)
        return self.report_and_save(jd, results)


def prompt_for_jd():
    """Ask the user for the JD path in the terminal until we get a real one."""
    while True:
        try:
            raw = input(cyan("→ path to the job description file (or 'q' to quit): "))
        except (EOFError, KeyboardInterrupt):
            print()
            return None
        # tidy up quotes/space that creep in when people paste a path
        path = raw.strip().strip('"').strip("'")
        if path.lower() in ("q", "quit", "exit", ""):
            return None
        if os.path.exists(path):
            return path
        print(red(f"   not found: {path} — try again."))


def main():
    banner()

    # Path can come from the command line as a shortcut...
    if len(sys.argv) >= 2:
        jd_path = sys.argv[1].strip().strip('"').strip("'")
        if not os.path.exists(jd_path):
            print(red(f"job description not found: {jd_path}"))
            sys.exit(1)
    # ...otherwise we just ask for it in the terminal.
    else:
        jd_path = prompt_for_jd()
        if jd_path is None:
            print(dim("   nothing to scout. bye."))
            sys.exit(0)

    workdir = os.path.dirname(os.path.abspath(jd_path)) or os.getcwd()
    agent = RecruiterAgent(workdir)
    agent.run(jd_path)


if __name__ == "__main__":
    main()