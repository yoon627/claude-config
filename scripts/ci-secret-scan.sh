#!/usr/bin/env bash
# ci-secret-scan.sh <base> [<head>] — CI backstop for the pre-push secret guard.
# Runs pre-commit-check.sh in pre-push mode over the commits of <head> that <base> lacks, so a
# push that skipped the local hook (never installed, --no-verify, pushed from another machine)
# is still caught after the fact. <base> goes to the guard as the destination's remote sha, the
# only thing it treats as already published; the checkout's tracking refs, which already hold
# the commits under test, are ignored. An empty or all-zero <base> (a new branch), or one this
# checkout does not have (a force push replaced it), scans the whole history of <head> — wider,
# never skipped. A shallow checkout is refused: its cut-off history would scan as if it were the
# root. Matched values are hidden: CI logs of a public repo are public.
set -euo pipefail

base="${1-}"
head_rev="${2:-HEAD}"
here="$(cd "$(dirname "$0")" && pwd)"

shallow="$(git rev-parse --is-shallow-repository)" ||
  { echo "ci-secret-scan: cannot tell whether this checkout is shallow" >&2; exit 1; }
if [ "$shallow" != false ]; then
  echo "ci-secret-scan: shallow checkout — fetch the full history (actions/checkout fetch-depth: 0)" >&2
  exit 1
fi
case "$(git rev-parse --show-object-format)" in sha256) hexsz=64 ;; *) hexsz=40 ;; esac
head_sha="$(git rev-parse --verify --quiet "${head_rev}^{commit}")" ||
  { echo "ci-secret-scan: cannot resolve $head_rev" >&2; exit 1; }
base_sha=""
if [ -n "$base" ] && ! [[ "$base" =~ ^0+$ ]]; then
  base_sha="$(git rev-parse --verify --quiet "${base}^{commit}")" ||
    echo "ci-secret-scan: base $base is not in this checkout (history rewritten by a force push?) — scanning the whole history" >&2
fi

echo "ci-secret-scan: ${base_sha:-(whole history)}..${head_sha}"
esc=$'\033'
# refs/heads/ci-scan, not main: the guard also blocks direct pushes to main/master.
printf 'refs/heads/ci-scan %s refs/heads/ci-scan %s\n' "$head_sha" "${base_sha:-$(printf '%0*d' "$hexsz" 0)}" |
  bash "$here/pre-commit-check.sh" pre-push 2>&1 |
  # Pattern names hold no ':' but may hold ')' ("GitHub PAT (fine)"). Hide the rest of the line —
  # a matched value can contain a tab — and put the colour reset back. The guard's "--no-verify"
  # hint is about a local hook and means nothing in CI.
  sed -E -e "s/(token pattern \([^:]*\)): .*/\1: (matched value hidden in CI log)${esc}[0m/" -e '/no-verify/d'
