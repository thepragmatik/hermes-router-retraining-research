#!/usr/bin/env python3
"""Mine session archives for task-type seeds. Output: JSON taxonomy of
(task_style, domain_hint, difficulty_hint) triples, counts + example verbs.
$0: sqlite + regex only, no model calls."""
import json, os, re, sqlite3
from collections import Counter

HOME = os.path.expanduser("~")
DBS = [os.path.join(HOME, ".hermes", "profiles", "uplift", "state.db")]
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                   "..", "..", "evidence", "gen_factory", "seed_taxonomy.json")
VERBS = re.compile(r"\b(write|fix|run|debug|design|explain|calculate|"
                   r"refactor|test|plan|compare|summarise|translate|optimi[sz]e)\b", re.I)

def main():
    verbs, styles = Counter(), Counter()
    for db in DBS:
        if not os.path.exists(db):
            continue
        con = sqlite3.connect(db)
        for (c,) in con.execute(
                "select content from messages where role='user' "
                "and length(content) between 40 and 800"):
            for m in VERBS.findall(c):
                verbs[m.lower()] += 1
            if re.search(r"\berror|traceback|exception\b", c, re.I):
                styles["debugging"] += 1
            elif re.search(r"\bplan|roadmap|phase\b", c, re.I):
                styles["planning"] += 1
            elif re.search(r"\bwrite|draft|memo|prompt\b", c, re.I):
                styles["writing"] += 1
            else:
                styles["other"] += 1
        con.close()
    tax = {"verbs": dict(verbs.most_common(20)), "styles": dict(styles),
           "source_dbs": ["profiles/uplift/state.db"]}  # relative label; never emit home paths
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    json.dump(tax, open(OUT, "w"), indent=1)
    print(json.dumps(tax, indent=1))

if __name__ == "__main__":
    main()
