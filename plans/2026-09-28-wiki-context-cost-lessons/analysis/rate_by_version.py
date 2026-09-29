"""Per Claude Code version: eligible calls (ctx>150K, same model/version, gap<=5m, no signal) and signal-free full-rewrite rate."""
import glob
import json
import os
import re
import time
from collections import defaultdict
from datetime import datetime

cutoff = time.time() - 30 * 86400
root = os.path.expanduser("~/.claude/projects")
CMD = re.compile(r"<command-name>(/[a-z:-]+)</command-name>")
seen = set()
stat = defaultdict(lambda: [0, 0, None, None])  # ver -> [eligible, rewrites, first_date, last_date]


def ts(rec):
    try:
        return datetime.fromisoformat(rec["timestamp"].replace("Z", "+00:00")).timestamp()
    except Exception:
        return None


for path in glob.glob(os.path.join(root, "*", "*.jsonl")):
    if os.path.getmtime(path) < cutoff:
        continue
    sig = False
    prev = None
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
                if CMD.search(s):
                    sig = True
                continue
            if typ == "system":
                if rec.get("subtype") not in ("turn_duration", "stop_hook_summary", None):
                    sig = True
                continue
            if typ != "assistant":
                continue
            msg = rec.get("message") or {}
            u = msg.get("usage")
            key = msg.get("id") or rec.get("requestId")
            if not u or not key or key in seen:
                continue
            seen.add(key)
            t, model, ver = ts(rec), msg.get("model"), rec.get("version")
            cc = u.get("cache_creation_input_tokens") or 0
            ctx = cc + (u.get("cache_read_input_tokens") or 0) + (u.get("input_tokens") or 0)
            if prev is not None:
                pt, pm, pv = prev
                gap = (t - pt) if (t and pt) else 0
                if not sig and pm == model and (not pv or pv == ver) and gap <= 300 and ctx > 150_000:
                    s_ = stat[ver]
                    s_[0] += 1
                    s_[1] += cc > 0.5 * ctx
                    d = rec.get("timestamp", "")[:10]
                    s_[2] = min(s_[2] or d, d)
                    s_[3] = max(s_[3] or d, d)
            sig = False
            prev = (t, model, ver)

for ver, (n, r, a, b) in sorted(stat.items(), key=lambda x: [int(p) for p in (x[0] or "0").split(".") if p.isdigit()]):
    if n >= 50:
        print(f"{ver:10} {a}~{b} eligible={n:6,} rewrites={r:3} rate={r / n:6.2%}")
