#!/usr/bin/env bash
# ci-secret-scan.sh <base> [<head>] — CI backstop for the pre-push secret guard.
# Runs pre-commit-check.sh in pre-push mode over the commits of <head> that <base> lacks, so a
# push that skipped the local hook (never installed, --no-verify, pushed from another machine)
# is still caught after the fact. The guard skips commits already on a remote-tracking ref, and
# in a CI checkout those refs hold the very commits under test. So the scan runs against a
# throwaway bare repo that borrows this checkout's objects and whose only remote-tracking ref is
# <base>. An empty or all-zero <base> (a new branch), or one this checkout does not have (a force
# push replaced it), scans the whole history of <head> — wider, never skipped. The checkout's own
# refs are never touched, and matched values are hidden: CI logs of a public repo are public.
set -euo pipefail

base="${1-}"
head_rev="${2:-HEAD}"
here="$(cd "$(dirname "$0")" && pwd)"

head_sha="$(git rev-parse --verify --quiet "${head_rev}^{commit}")" ||
  { echo "ci-secret-scan: cannot resolve $head_rev" >&2; exit 1; }
base_sha=""
if [ -n "$base" ] && ! [[ "$base" =~ ^0+$ ]]; then
  base_sha="$(git rev-parse --verify --quiet "${base}^{commit}")" ||
    echo "ci-secret-scan: base $base is not in this checkout (history rewritten by a force push?) — scanning the whole history" >&2
fi

scan_dir="$(mktemp -d)"
trap 'rm -rf "$scan_dir"' EXIT
git init -q --bare "$scan_dir/scan.git"
objects="$(cd "$(git rev-parse --git-common-dir)/objects" && pwd -P)"
printf '%s\n' "$objects" > "$scan_dir/scan.git/objects/info/alternates"
[ -n "$base_sha" ] && git --git-dir="$scan_dir/scan.git" update-ref refs/remotes/ci-base/base "$base_sha"

echo "ci-secret-scan: ${base_sha:-(whole history)}..${head_sha}"
esc=$'\033'
# refs/heads/ci-scan, not main: the guard also blocks direct pushes to main/master.
printf 'refs/heads/ci-scan %s refs/heads/ci-scan %s\n' "$head_sha" "${base_sha:-0000000000000000000000000000000000000000}" |
  GIT_DIR="$scan_dir/scan.git" bash "$here/pre-commit-check.sh" pre-push 2>&1 |
  # Pattern names hold no ':' but may hold ')' ("GitHub PAT (fine)"). Hide the rest of the line —
  # a matched value can contain a tab — and put the colour reset back. The guard's "--no-verify"
  # hint is about a local hook and means nothing in CI.
  sed -E -e "s/(token pattern \([^:]*\)): .*/\1: (matched value hidden in CI log)${esc}[0m/" -e '/no-verify/d'
