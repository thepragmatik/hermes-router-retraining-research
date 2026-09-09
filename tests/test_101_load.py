"""T036 load test: >=1,000 events, measure p50/p95 decision-logging overhead.

Prereg target (spec NFR): p95 < 5 ms locally excluding fsync/network.
"""
import os
import statistics
import sys
import time

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO)

from telemetry.decision_log import DecisionLogger, read_decisions  # noqa: E402
from telemetry.schema import make_decision_event  # noqa: E402

N_EVENTS = 1200


def test_load_1000_events_overhead(tmp_path):
    lg = DecisionLogger(log_dir=str(tmp_path))
    overhead_ms = []
    for i in range(N_EVENTS):
        prompt = f"load-test synthetic prompt {i % 50}"  # 50 distinct prompts, duplicates included
        d = make_decision_event(prompt, confidence=0.5 + (i % 10) / 100.0,
                                chosen_action="strong" if i % 3 == 0 else "weak")
        t0 = time.perf_counter()
        ok = lg.log_decision(d)
        overhead_ms.append((time.perf_counter() - t0) * 1000.0)
        assert ok is True
    lg.close()

    p50 = statistics.quantiles(overhead_ms, n=100)[49]
    p95 = statistics.quantiles(overhead_ms, n=100)[94]
    recs, quar = read_decisions(lg.path)
    assert len(recs) == N_EVENTS
    assert quar == []
    assert len({r["event_id"] for r in recs}) == N_EVENTS
    # Frozen NFR: p95 < 5 ms
    assert p95 < 5.0, f"p95 logging overhead {p95:.3f} ms >= 5 ms"
    print(f"\nT036 load: {N_EVENTS} events, p50={p50:.3f} ms, p95={p95:.3f} ms, "
          f"max={max(overhead_ms):.3f} ms")
