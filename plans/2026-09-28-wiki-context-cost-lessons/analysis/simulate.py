"""Replay main-session call sequences under an auto-compact window W and estimate API-equivalent cost change.

Model: context grows by the observed per-call delta; when simulated context would exceed W, a compaction
happens (one extra call reading the context + ~summary output) and context resets to P (measured post-compact
size) plus the delta. Large observed rewrites (cache misses) are scaled to the simulated context size.
Counts/sizes only.
"""
import glob
import json
import os
import statistics
import sys
import time

cutoff = time.time() - 30 * 86400
root = os.path.expanduser("~/.claude/projects")
# $/MTok: input, output, cache_read, write_1h
PRICE = {"claude-opus-5-5": (4, 20, 0.20, 8), "claude-opus-5": (5, 25, 0.50, 10),
         "claude-fable-5-1": (10, 50, 0.25, 20), "claude-opus-4-8": (5, 25, 0.50, 10),
         "claude-sonnet-5": (2, 10, 0.20, 4), "claude-haiku-4-5-20251001": (1, 5, 0.10, 2)}
SUMMARY_OUT = 12_000  # assumed compaction summary output tokens (⚠️ assumption)

sessions = []
post_compact = []
seen = set()
for path in glob.glob(os.path.join(root, "*", "*.jsonl")):
    if os.path.getmtime(path) < cutoff:
        continue
    seq = []
    after_compact = False
    with open(path, encoding="utf-8", errors="replace") as f:
        for line in f:
            if '"compact_boundary"' in line:
                after_compact = True
            try:
                rec = json.loads(line)
            except ValueError:
                continue
            if rec.get("type") != "assistant":
                continue
            msg = rec.get("message") or {}
            u = msg.get("usage")
            key = msg.get("id") or rec.get("requestId")
            if not u or not key or key in seen or msg.get("model") not in PRICE:
                continue
            seen.add(key)
            cc = u.get("cache_creation_input_tokens") or 0
            cr = u.get("cache_read_input_tokens") or 0
            inp = u.get("input_tokens") or 0
            ctx = cc + cr + inp
            if after_compact:
                post_compact.append(ctx)
                after_compact = False
            seq.append((msg["model"], ctx, cc, u.get("output_tokens") or 0))
    if seq:
        sessions.append(seq)

P = int(statistics.median(post_compact)) if post_compact else 60_000
print(f"sessions={len(sessions)} post-compaction ctx median P={P:,} (n={len(post_compact)})")


def cost(model, cr, cw, out):
    p = PRICE[model]
    return (cr * p[2] + cw * p[3] + out * p[1]) / 1e6


def run(W):
    total = 0.0
    compactions = 0
    for seq in sessions:
        s = None
        prev_ctx = None
        for model, ctx, cc, out in seq:
            if s is None:
                s = ctx
            else:
                delta = ctx - prev_ctx
                if delta < 0:  # real compaction/reset happened
                    s = ctx if W is None else min(ctx, s)
                else:
                    s = s + delta
            if W is not None and s > W:
                compactions += 1
                total += cost(model, s, 0, SUMMARY_OUT)  # summarization call
                s = P + max(ctx - prev_ctx, 0) if prev_ctx is not None else P
                cw = s  # new context written after compaction
            else:
                # observed write, scaled if it was a large rewrite
                cw = cc if cc < 0.5 * ctx else min(cc, s)
            cr = max(s - cw, 0)
            total += cost(model, cr, cw, out)
            prev_ctx = ctx
    return total, compactions


base, _ = run(None)
print(f"replayed baseline (as observed) ${base:,.0f}")
for W in (200_000, 300_000, 400_000, 500_000, 700_000):
    t, n = run(W)
    print(f"W={W // 1000:>4}K  ${t:8,.0f}  change={(t - base) / base:6.1%}  compactions={n:5} ({n / len(sessions):.1f}/session)")
