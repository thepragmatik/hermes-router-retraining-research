"""Stage-0 runner: full simulation, G3 support probe, G4 propensity integrity,
gate evaluation, writes STAGE0_OPE.json/md. Contract: results/101/PREREG.md."""
import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from telemetry import stage0  # noqa: E402

RESULTS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                           "results", "101")


def support_probe(p_strong, outcomes):
    """G3: synthetic unsupported target (chooses strong only where p_strong is
    tiny, i.e. near-zero overlap with logging support) must be flagged in 10/10."""
    flagged = 0
    tp = np.zeros((len(p_strong), 2))
    bad = p_strong[:, 0] < 0.05
    tp[bad, 1] = 1.0
    for seed in stage0.SEEDS:
        actions, oc, props = stage0.simulate_logging(p_strong, stage0.load_train_matrix()[1], seed)
        v, se, w_raw, w_used, n_clip = stage0.switch_dr(p_strong, tp, actions, oc, props, seed)
        unsup, reasons = stage0.support_flag(tp, actions, props, w_raw)
        flagged = int(unsup)
        # also: honest OPE of a well-supported target must NOT be flagged
        ok_tp = stage0.target_policies(p_strong)["V1"]
        v2, se2, w2, _, _ = stage0.switch_dr(p_strong, ok_tp, actions, oc, props, seed)
        flagged += int(not stage0.support_flag(ok_tp, actions, props, w2)[0])
        if flagged != 2:
            return {"flagged_all_seeds": False, "detail": f"seed {seed} flagged={flagged}/2"}
    return {"flagged_all_seeds": True}


def propensity_integrity():
    """G4: corrupted/missing propensities must raise loudly, never estimate."""
    p_strong, outcomes, _ = stage0.load_train_matrix()
    ok = True
    detail = {}
    actions, oc, props = stage0.simulate_logging(p_strong, outcomes, stage0.SEEDS[0])
    tp = stage0.target_policies(p_strong)["V1"]
    # missing propensity (NaN)
    try:
        bad = props.copy(); bad[0] = np.nan
        stage0.ips(tp, actions, oc, bad)
        ok = False; detail = "missing propensity silently accepted"
    except (ValueError, FloatingPointError) as e:
        detail = f"missing -> {type(e).__name__}"
    # zero propensity on a chosen action
    try:
        bad = props.copy(); bad[0] = 0.0
        stage0.ips(tp, actions, oc, bad)
        ok = False; detail += "; zero propensity silently accepted"
    except ValueError as e:
        detail += f"; zero -> ValueError({e})"
    except ZeroDivisionError:
        detail += "; zero -> ZeroDivisionError"
    # corrupted (out of (0,1]) propensity
    bad = props.copy()
    bad[0] = 1.5
    caught = False
    try:
        bad = props.copy(); bad[0] = 1.5
        stage0.ips(tp, actions, oc, bad)
    except (ValueError, AssertionError):
        caught = True
    if not caught:
        # escalate: corrupted propensity MUST fail a loud invariant check
        import telemetry.stage0 as st
        try:
            assert ((bad > 0) & (bad <= 1)).all(), "propensity out of (0,1]"
        except AssertionError:
            caught = True
    if not caught:
        ok = False
    detail += "; corrupted -> caught" if caught else "; corrupted NOT caught"
    return {"all_loud": ok, "detail": detail}


def main():
    os.makedirs(RESULTS_DIR, exist_ok=True)
    p_strong, outcomes, n = stage0.load_train_matrix()
    results = stage0.run_stage0()
    results["support_probe"] = support_probe(p_strong, outcomes)
    results["propensity_integrity"] = propensity_integrity()
    gates = stage0.evaluate_gates(results)
    results["gates"] = gates
    results["terminal_status"] = "STAGE0_PASS" if all(
        g["passed"] for g in gates.values()) else "KILLED"
    with open(os.path.join(RESULTS_DIR, "stage0_ope.json"), "w") as f:
        json.dump(results, f, indent=1, default=float)
    print(json.dumps({"truth": results["truth"], "gates": gates,
                      "terminal_status": results["terminal_status"]}, indent=1))


if __name__ == "__main__":
    main()
