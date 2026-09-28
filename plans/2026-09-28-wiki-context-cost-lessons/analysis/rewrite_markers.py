"""Explain full cache rewrites (cc > 50% of ctx, ctx > 60K) in main sessions by what happened since the previous call.

Signals: model change, compaction, slash command, system subtype, Claude Code version change (restart/resume),
cwd change, idle gap. Also: rewrite rate after each signal vs. baseline. Counts only.
"""
import glob
import json
import os
import re
import time
from collections import Counter, defaultdict
from datetime import datetime

cutoff = time.time() - 30 * 86400
root = os.path.expanduser("~/.claude/projects")
CMD = re.compile(r"<command-name>(/[a-z:-]+)</command-name>")
W1H = {"claude-opus-5-5": 8, "claude-opus-5": 10, "claude-fable-5-1": 20, "claude-opus-4-8": 10,
       "claude-sonnet-5": 4, "claude-haiku-4-5-20251001": 2}

seen = set()
first_cause = Counter()
first_cause_usd = defaultdict(float)
after = defaultdict(lambda: [0, 0])  # signal -> [calls after it, rewrites]
baseline = [0, 0]


def ts(rec):
    try:
        return datetime.fromisoformat(rec["timestamp"].replace("Z", "+00:00")).timestamp()
    except Exception:
        return None


for path in glob.glob(os.path.join(root, "*", "*.jsonl")):
    if os.path.getmtime(path) < cutoff:
        continue
    sig = set()
    prev = None  # (t, model, version, cwd)
    with open(path, encoding="utf-8", errors="replace") as f:
        for line in f:
            try:
                rec = json.loads(line)
            except ValueError:
                continue
            typ = rec.get("type")
            if typ == "user":
                c = (rec.get("message") or {}).get("content")
                s = c if isinstance(c, str) else " ".join(
                    x.get("text", "") for x in (c or []) if isinstance(x, dict) and x.get("type") == "text")
                for m in CMD.findall(s):
                    sig.add("cmd" + m)
                continue
            if typ == "system":
                st = rec.get("subtype") or ""
                if st and st not in ("turn_duration", "stop_hook_summary"):
                    sig.add("sys:" + st)
                continue
            if typ != "assistant":
                continue
            msg = rec.get("message") or {}
            u = msg.get("usage")
            key = msg.get("id") or rec.get("requestId")
            if not u or not key or key in seen:
                continue
            seen.add(key)
            t, model, ver, cwd = ts(rec), msg.get("model"), rec.get("version"), rec.get("cwd")
            cc = u.get("cache_creation_input_tokens") or 0
            ctx = cc + (u.get("cache_read_input_tokens") or 0) + (u.get("input_tokens") or 0)
            if prev is not None:
                pt, pm, pv, pc = prev
                if pm != model:
                    sig.add("model-change")
                if pv and ver and pv != ver:
                    sig.add("version-change")
                if pc and cwd and pc != cwd:
                    sig.add("cwd-change")
                gap = (t - pt) if (t and pt) else 0
                if gap > 3600:
                    sig.add("gap>1h")
                elif gap > 300:
                    sig.add("gap5-60m")
                rewrite = ctx > 60_000 and cc > 0.5 * ctx
                if sig:
                    for s_ in sig:
                        after[s_][0] += 1
                        after[s_][1] += rewrite
                else:
                    baseline[0] += 1
                    baseline[1] += rewrite
                if rewrite:
                    order = ["model-change", "sys:compact_boundary", "version-change", "gap>1h", "gap5-60m",
                             "cwd-change"]
                    cause = next((o for o in order if o in sig), None)
                    if cause is None:
                        cmds = sorted(x for x in sig if x.startswith("cmd/") or x.startswith("sys:"))
                        cause = cmds[0] if cmds else ("none(gap<1m)" if gap < 60 else "none(gap1-5m)")
                    first_cause[cause] += 1
                    first_cause_usd[cause] += cc * W1H.get(model, 8) / 1e6
            sig = set()
            prev = (t, model, ver, cwd)

print(f"baseline (no signal since previous call): calls={baseline[0]:,} rewrites={baseline[1]} "
      f"({baseline[1] / max(baseline[0], 1):.2%})")
print("rewrite rate after signal (signals seen >= 5 times):")
for s_, (n, r) in sorted(after.items(), key=lambda x: -x[1][1]):
    if n >= 5:
        print(f"  {s_:28} calls={n:6,} rewrites={r:4} ({r / n:6.1%})")
print("rewrites by first explaining signal (~$ at 1h write price):")
for c, n in first_cause.most_common():
    print(f"  {c:28} {n:4}  ~${first_cause_usd[c]:7,.0f}")
