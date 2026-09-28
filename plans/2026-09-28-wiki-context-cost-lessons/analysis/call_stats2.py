"""Global-dedup per-call context stats, >200K share, per-session max, compaction counts (counts only)."""
import glob
import json
import os
import sys
import time
from collections import defaultdict

DAYS = int(sys.argv[1]) if len(sys.argv) > 1 else 30
cutoff = time.time() - DAYS * 86400
root = os.path.expanduser("~/.claude/projects")

seen = set()
calls = {"main": [], "sub": []}
sess_max = []
compact_sessions = 0
compact_events = 0

for path in glob.glob(os.path.join(root, "**", "*.jsonl"), recursive=True):
    if os.path.getmtime(path) < cutoff:
        continue
    kind = "sub" if "/subagents/" in path else "main"
    smax = 0
    ncompact = 0
    with open(path, encoding="utf-8", errors="replace") as f:
        for line in f:
            if '"compact_boundary"' in line or '"isCompactSummary":true' in line:
                ncompact += 1
            try:
                rec = json.loads(line)
            except ValueError:
                continue
            if rec.get("type") != "assistant":
                continue
            msg = rec.get("message") or {}
            u = msg.get("usage")
            if not u:
                continue
            key = msg.get("id") or rec.get("requestId")
            if not key or key in seen:
                continue
            seen.add(key)
            ctx = (u.get("input_tokens") or 0) + (u.get("cache_creation_input_tokens") or 0) + (u.get("cache_read_input_tokens") or 0)
            if ctx:
                calls[kind].append(ctx)
                smax = max(smax, ctx)
    if kind == "main" and smax:
        sess_max.append(smax)
        if ncompact:
            compact_sessions += 1
            compact_events += ncompact

for k, v in calls.items():
    v.sort()
    tot = sum(v)
    over = [x for x in v if x > 200_000]
    print(f"{k:4} calls={len(v):7,} total={tot:15,} mean={tot // max(len(v), 1):9,} median={v[len(v)//2]:9,} "
          f">200K calls={len(over) / len(v):5.1%} of_tokens={sum(over) / tot:5.1%}")
sess_max.sort()
n = len(sess_max)
print(f"main sessions={n} max-ctx median={sess_max[n//2]:,} p75={sess_max[n*3//4]:,} p90={sess_max[n*9//10]:,} "
      f"sessions>500K={sum(1 for x in sess_max if x > 500_000)} >800K={sum(1 for x in sess_max if x > 800_000)}")
print(f"sessions with compaction markers={compact_sessions} (marker lines {compact_events})")
allc = calls["main"] + calls["sub"]
print(f"ALL calls={len(allc):,} total_ctx={sum(allc):,}")
for base in (20_000,):
    print(f"CLAUDE.md {base:,} tok share: main-only={base * len(calls['main']) / sum(allc):5.1%} "
          f"main+sub={base * len(allc) / sum(allc):5.1%}")
