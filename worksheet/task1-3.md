# Tutorial 6 worksheet: serving patterns

**Name / ชื่อ:** (fill your name)

**Student ID / รหัสนิสิต:** (fill your ID)

This is **individual work**: each student completes and submits their own copy, in their own fork.

*งานนี้เป็น**งานเดี่ยว** นิสิตแต่ละคนทำและส่งงานของตัวเอง โดยใช้ forked repository ของตัวเอง*

Copy result rows from `results/runs.csv` (or the load test's output) into the tables. Keep answers short: one to three sentences each. Answer in Thai or English.

## Task 0: Baseline (copy the baseline results from `results/runs.csv` here)

| Run | p50 ms | p95 ms | accuracy | large calls |
|---|---|---|---|---|
| t0-large | 482 | 585 | 93.5% | 100% |
| t0-small | 23 | 41 | 72.5% | 0% |

**Q0.** What does the large model buy, and what does it cost?

*large model ให้อะไรเพิ่ม และต้องแลกด้วยอะไร*

> The large model buys ~21 percentage points of accuracy (93.5% vs 72.5%). It costs ~20× higher latency (p50 482 ms vs 23 ms) and 100% of the expensive large-model calls (vs 0%).

## Task 1: Fallback prediction (copy the Task 1 results from `results/runs.csv` here)

| Run | run time (s) | p50 ms | p95 ms | errors | pending | accuracy |
|---|---|---|---|---|---|---|
| t1-before | ~20–40+ (expected without timeout) | — | high | ~20 | 0 | ~93% |
| t1-after | 10.1 | 443 | 1005 | 0 | 18 | 92.9% |

*(Note: because the fallback was already implemented when measuring, both measured runs show pending>0 and errors=0. Without the 1 s timeout, the ~10% hung calls would become client-side errors after 10 s and the whole run would take much longer.)*

**Q1.1** In `t1-before`, p50 can look *better* than the baseline. Why is p50 misleading here? Which column tells the real story?

> p50 only looks at the middle of the distribution; the hung requests are in the tail, so the median can still look fine while many users wait 10 s and fail. The real story is in `errors` (and wall-clock run time / p95).

**Q1.2** The hang affects only 10% of large-model calls. Why is it worse for the system than 10% of reviews being slow? Think about what a waiting request holds on to in the review service and the gateway.

> A hanging request holds an open connection, a worker/thread, and a slot in the concurrency limit of the review service and the gateway. Those resources are not free for the other 90% of reviews, so the whole system backs up and latency/error rate rises far beyond the original 10%.

**Q1.3** Pending reviews have no label. Suggest what should happen to them, and name the topology from the lecture that does it.

> Queue or store them and score them later in a batch / asynchronous job (e.g. overnight). That is the **asynchronous / batch** topology (T4).

**Q1.4** We chose a 1-second timeout. What goes wrong if it is 0.1 s? And if it is 10 s?

> 0.1 s: many normal large-model calls (~200 ms) would time out and become pending, so accuracy drops and the batch job is overloaded. 10 s: a hang still blocks a worker for 10 s, so the system remains vulnerable to resource exhaustion and QR1/QR2 are violated.

## Task 2: Cascade (copy the Task 2 results from `results/runs.csv` here)

| Run | threshold | p50 ms | p95 ms | accuracy | large calls |
|---|---|---|---|---|---|
| t2-0.6 | 0.6 | 9 | 611 | 91.5% | 38% |
| t2-0.7 | 0.7 | 395 | 569 | 93.0% | 53% |
| t2-0.8 | 0.8 | 479 | 642 | 93.5% | 64% |
| t2-0.9 | 0.9 | 476 | 596 | 93.5% | 77% |

**Q2.1** Which threshold would you deploy for CampusEats, and why? Name the quality you give up.

> Threshold **0.7**: accuracy stays ≥ 90% (QR3) at 93.0% while cutting large-model cost roughly in half (53%). Higher thresholds spend more money for almost no accuracy gain. We give up a little accuracy versus pure large (93.5% → 93.0%) and accept that p50 is still higher than pure small.

**Q2.2** Look at p50 and p95 for your threshold. Why does the cascade help p50 much more than p95?

> Most reviews are “easy” and are answered by the fast small model, so the median (p50) drops a lot. The hard reviews still go to the large model (~200 ms + queueing), so the tail (p95) stays close to the pure-large latency.

**Q2.3** The cascade trusts the small model's confidence. Give one situation where that trust is misplaced, and its effect on users.

> The small model can be confidently wrong on negations or “but” contrasts (e.g. “not bad”, “good but cold”). A high-confidence wrong label is returned without escalation, so owners may miss real complaints or get false alerts.

## Task 3: Cached predictions (copy the Task 3 results from `results/runs.csv` here)

| Run | p50 ms | p95 ms | accuracy | large calls | cache hits |
|---|---|---|---|---|---|
| t3-cache | 5 | 555 | 93.0% | 38% | 35% |

**Q3.1** Which reviews benefit from the cache, and which never will?

> Repeated / near-duplicate review texts (same wording ignoring case and spacing) benefit. Unique, one-off reviews never hit the cache.

**Q3.2** Next week you deploy a better large model. What must happen to the cache, and how would you design for it?

> Invalidate (flush) the cache, otherwise stale answers from the old model keep being served. Design: version the cache key with the model version / model id, or clear the cache on model deployment.

## Debrief

**Q4.** Name one thing you learned from these measurements that the lecture did not cover.

> Cascade improves the median latency far more than the tail: the remaining large-model calls still dominate p95, so capacity planning and QR1 must still be driven by the expensive path, not by the average.
