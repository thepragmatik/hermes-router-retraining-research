# gen_factory ledger report — $/usable-label

Decision metric: `cost_per_usable_label_usd` (total ledgered cost
divided by labels produced). All cost math from ledger rows only;
both-fail items are labeled separately, never as weak_ok.

## Rung totals (status: ok)

| metric | value |
|---|---|
| n_generated | 801 |
| n_items_accepted | 327 |
| n_parse_rejected | 271 |
| n_other_gen_rejected | 154 |
| n_dedup_rejected | 49 |
| n_labels_written | 327 |
| n_labeled | 346 |
| weak_ok_count | 179 |
| need_strong_count | 18 |
| both_fail_count | 149 |
| strong_calls_made | 167 |
| total_est_cost_usd | 0.03409278 |
| cost_per_usable_label_usd | 0.00009853 |
| cost_per_weak_ok_usd | 0.00019046 |
| unpriced_call_count | 19 |

## Per batch

| id | n_labeled | weak_ok | need_strong | both_fail | strong_calls | total_est_cost_usd | cost_per_usable_label_usd |
|---|---|---|---|---|---|---|---|

| r1_b8919 | 98 | 16 | 9 | 73 | 82 | 0.00936907 | 0.0000956 |
| r2_b1788835509_18671 | 48 | 29 | 2 | 17 | 19 | 0.00543428 | 0.00011321 |
| r3_b1788846596_21839 | 54 | 30 | 0 | 24 | 24 | 0.00580293 | 0.00010746 |
| r4_b1788858717_26041 | 70 | 38 | 3 | 29 | 32 | 0.00775505 | 0.00011079 |
| r5_b1788873429_32834 | 18 | 16 | 0 | 2 | 2 | 0.00099121 | 0.00005507 |
| r6_b1788887455_38941 | 32 | 26 | 4 | 2 | 6 | 0.0030741 | 0.00009607 |
| r7_b1788903723_47290 | 26 | 24 | 0 | 2 | 2 | 0.00166614 | 0.00006408 |

## Per rung

| id | n_labeled | weak_ok | need_strong | both_fail | strong_calls | total_est_cost_usd | cost_per_usable_label_usd |
|---|---|---|---|---|---|---|---|

| r1 | 98 | 16 | 9 | 73 | 82 | 0.00936907 | 0.0000956 |
| r2 | 48 | 29 | 2 | 17 | 19 | 0.00543428 | 0.00011321 |
| r3 | 54 | 30 | 0 | 24 | 24 | 0.00580293 | 0.00010746 |
| r4 | 70 | 38 | 3 | 29 | 32 | 0.00775505 | 0.00011079 |
| r5 | 18 | 16 | 0 | 2 | 2 | 0.00099121 | 0.00005507 |
| r6 | 32 | 26 | 4 | 2 | 6 | 0.0030741 | 0.00009607 |
| r7 | 26 | 24 | 0 | 2 | 2 | 0.00166614 | 0.00006408 |
