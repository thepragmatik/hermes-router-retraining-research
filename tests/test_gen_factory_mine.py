import json, os, sqlite3, sys
REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def test_seed_taxonomy_exists_and_has_verbs():
    p = os.path.join(REPO, "evidence", "gen_factory", "seed_taxonomy.json")
    if not os.path.exists(p):
        os.makedirs(os.path.dirname(p), exist_ok=True)
        sys.path.insert(0, os.path.join(REPO, "experiments", "gen_factory"))
        import mine_seed_taxonomy
        mine_seed_taxonomy.OUT = p
        mine_seed_taxonomy.main()
    tax = json.load(open(p))
    assert sum(tax["styles"].values()) > 0
    assert len(tax["verbs"]) > 0
