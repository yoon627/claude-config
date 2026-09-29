"""API-equivalent cost breakdown (deduped) + large cache-write (miss) classification. Counts only."""
import glob
import json
import os
import sys
import time
from collections import defaultdict
from datetime import datetime

DAYS = int(sys.argv[1]) if len(sys.argv) > 1 else 30
cutoff = time.time() - DAYS * 86400
root = os.path.expanduser("~/.claude/projects")

# $/MTok: input, output, cache_read, write_5m, write_1h  (bundled claude-api skill, 2026-09)
PRICE = {
    "claude-opus-5-5": (4, 20, 0.20, 5, 8),
    "claude-opus-5": (5, 25, 0.50, 6.25, 10),
    "claude-fable-5-1": (10, 50, 0.25, 12.5, 20),
    "claude-opus-4-8": (5, 25, 0.50, 6.25, 10),
    "claude-sonnet-5": (2, 10, 0.20, 2.5, 4),
    "claude-haiku-4-5-20251001": (1, 5, 0.10, 1.25, 2),
}
seen = set()
cost = defaultdict(float)  # component -> $
tok = defaultdict(int)
miss = defaultdict(lambda: [0, 0, 0.0])  # class -> [count, tokens, $]
BIG = 50_000


def ts(rec):
    t = rec.get("timestamp")
    try:
        return datetime.fromisoformat(t.replace("Z", "+00:00")).timestamp()
    except Exception:
        return None


for path in glob.glob(os.path.join(root, "**", "*.jsonl"), recursive=True):
    if os.path.getmtime(path) < cutoff:
        continue
    kind = "sub" if "/subagents/" in path else "main"
    prev_t = None
    first = True
    with open(path, encoding="utf-8", errors="replace") as f:
        for line in f:
            try:
                rec = json.loads(line)
            except ValueError:
                continue
            if rec.get("type") != "assistant":
                continue
            msg = rec.get("message") or {}
            u = msg.get("usage")
            key = msg.get("id") or rec.get("requestId")
            if not u or not key or key in seen:
                continue
            seen.add(key)
            p = PRICE.get(msg.get("model"))
            if not p:
                continue
            cc = u.get("cache_creation_input_tokens") or 0
            det = u.get("cache_creation") or {}
            c1h = det.get("ephemeral_1h_input_tokens")
            c5m = det.get("ephemeral_5m_input_tokens")
            if c1h is None and c5m is None:
                c1h, c5m = cc, 0  # assume 1h when no breakdown
            c = {
                "input": (u.get("input_tokens") or 0) * p[0],
                "output": (u.get("output_tokens") or 0) * p[1],
                "cache_read": (u.get("cache_read_input_tokens") or 0) * p[2],
                "cache_write": (c5m or 0) * p[3] + (c1h or 0) * p[4],
            }
            for k, v in c.items():
                cost[f"{kind}:{k}"] += v / 1e6
            tok[f"{kind}:cache_write"] += cc
            t = ts(rec)
            if cc >= BIG:
                if first:
                    cls = f"{kind}:session-start"
                elif prev_t and t and t - prev_t > 3600:
                    cls = f"{kind}:after-idle>1h"
                elif prev_t and t and t - prev_t > 300:
                    cls = f"{kind}:after-idle5-60m"
                else:
                    cls = f"{kind}:other(<5m gap)"
                m = miss[cls]
                m[0] += 1
                m[1] += cc
                m[2] += c["cache_write"] / 1e6
            first = False
            prev_t = t or prev_t

total = sum(cost.values())
print(f"API-equivalent total ${total:,.0f} ({DAYS}d)")
for k, v in sorted(cost.items(), key=lambda x: -x[1]):
    print(f"  {k:22} ${v:9,.0f}  {v / total:5.1%}")
print(f"large cache writes (>= {BIG:,} tokens in one call):")
for k, (n, t_, d) in sorted(miss.items(), key=lambda x: -x[1][2]):
    print(f"  {k:28} calls={n:5,} tokens={t_:13,} ${d:8,.0f}  {d / total:5.1%}")
