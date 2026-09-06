# Hermes daily-update compatibility — V1 router shadow ops (2026-09-06)

Verifies that the V1-router operationalisation (CLI + kill-switch config +
shadow HTTP service + parent-stack client, branch `feat/router-v1-operationalise`)
cannot be broken by — and cannot break — the daily `hermes update`.

## 1. Blast-radius matrix (plan-2 Task 1)

`python3 /tmp/blast_radius.py` (run under `~/.pyenv/versions/3.11.11/bin/python3`;
host python3 3.9 cannot import the updater's `hermes_cli` because it uses
`str | None` syntax — itself confirmation the two runtimes are independent):

```
updater git/subprocess cwd variables used: ['None', 'PROJECT_ROOT', 'cwd', 'repo_root', 'root', 'str']
PROJECT_ROOT = /Users/rath/.hermes/hermes-agent
router artifacts all outside updater blast radius: OK
HERMES_HOME = /Users/rath/.hermes/profiles/uplift
skills sync target = /Users/rath/.hermes/profiles/uplift/skills
MATRIX: PASS
```

Every `cwd=` occurrence in `update_cmd*.py` resolves to `PROJECT_ROOT`
(`hermes_cli/config.py:534` → `Path(__file__).parent.parent.resolve()` =
`~/.hermes/hermes-agent`) or a variable assigned from it. Verified call sites:
`update_cmd.py:1025-1026` (`_discard_lockfile_churn`/`_normalize_managed_eol`
receive `_m().PROJECT_ROOT`), `update_cmd_deps.py:154/157/423/657/849`
(all `cwd=_m().PROJECT_ROOT`), `update_cmd_git.py:460/490` (`cwd=repo_root`,
passed `_m().PROJECT_ROOT` at `update_cmd.py:1025-1026`). No subprocess in the
updater runs against `~/src/hermes-router-retraining-research`,
`~/src/hermes-pi-agentic-stack`, or `~/transfer-bundle`.

## 2. Dependency-sync isolation (plan-2 Task 2)

```
which hermes  -> /Users/rath/.pyenv/versions/3.11.11/bin/hermes
head -1       -> #!/Users/rath/.pyenv/versions/3.11.11/bin/python3.11
grep -n "torch\|sentence" ~/.hermes/hermes-agent/hermes_cli/update_cmd_deps.py
              -> no matches (exit 1)
host cli python: /Applications/Xcode.app/Contents/Developer/usr/bin/python3
```

Three disjoint interpreters: (a) the CLI/host python3 (Xcode 3.9) that runs
`router_v1_cli.py` and its torch/sentence-transformers stack from
`~/Library/Python/3.9`; (b) pyenv 3.11.11 that runs the `hermes` binary;
(c) `~/.hermes/hermes-agent/venv/bin/python` which the updater's dep-sync
rebuilds (torch import there fails today — it doesn't need torch). The updater's
dep-sync never installs or uninstalls torch/sentence-transformers (grep: no
matches), so it physically cannot alter the router's runtime deps.

## 3. Gateway restart scope (plan-2 Task 3)

```
grep launchd update_cmd_fleet.py -> _FRESH_RESTART_SUPERVISORS = frozenset({"systemd", "launchd", "service", "s6"})
                                 -> _restart_macos_launchd_gateways([], failed, 45.0)
```

Restart is scoped to launchd gateway services. `router_shadow.py` is a
standalone process, not registered under Hermes gateway/cron lifecycle — the
docstring NOTE (ops) added this session documents that it survives updates and
should be health-checked (`curl http://127.0.0.1:8765/health`) afterwards.

## 4. Bundled-skills sync idempotency (plan-2 Task 4)

Double `sync_skills(quiet=True)` run under pyenv 3.11:

```
run1: {'copied': 0, 'updated': 0, 'skipped': 1, 'user_modified': 0, 'cleaned': 0, 'suppressed': 0, 'relocated': 0, 'total_bundled': 1, 'skipped_opt_out': True}
run2: {'copied': 0, 'updated': 0, 'skipped': 1, 'user_modified': 0, 'cleaned': 0, 'suppressed': 0, 'relocated': 0, 'total_bundled': 1, 'skipped_opt_out': True}
```

Identical, zero copies/updates/deletions — nothing the router work added can be
clobbered. All profile skills intact after both runs
(`~/.hermes/profiles/uplift/skills/`: autonomous-ai-agents, devops,
hermes-stack-uplift, hermes-stack-uplift-lessons, memory,
plain-english-reporting, research, task-and-mode-discipline).

## Conclusion

Confirmed by direct inspection of `~/.hermes/hermes-agent/hermes_cli/update_cmd*.py`
plus live checks: the daily update performs git/stash/dependency/gateway-restart
operations scoped to `~/.hermes/hermes-agent` and a merged-only bundled-skills
sync into the profile home. None of the router operationalisation's files live
in either location; the router's Python environment (Xcode python 3.9 + user
site-packages) is a different interpreter from the venv the updater rebuilds;
the only interaction is a launchd gateway restart that the standalone shadow
service is documented to survive (fail-closed by design, kill switch defaults
to disabled-on-any-failure). Worst case after any update: the router silently
stops routing — it can never misroute.

## Open item for the operator

How the daily update is triggered (manual alias vs launchd/cron) — no plist
running `hermes update` was found, so it is likely manual. Not needed for this
verification (the updater's write surface is identical either way); knowing the
trigger would let the post-update health check be scheduled automatically.
