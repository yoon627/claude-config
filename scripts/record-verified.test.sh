#!/usr/bin/env bash
# Tests for the record-verified job in .github/workflows/lint.yml. The job holds a write token, so
# it runs no repository code; this test takes its `run` block verbatim from the workflow and runs
# it against a fake `gh` that models main's history and the ci/verified record.
set -u
DIR="$(cd "$(dirname "$0")" && pwd)"
WORKFLOW="$DIR/../.github/workflows/lint.yml"
command -v jq >/dev/null || { echo 'record-verified.test.sh: jq is required (the job builds its API bodies with it)'; exit 1; }
T="$(mktemp -d)"
trap 'rm -rf "$T"' EXIT
pass=0; fail=0

# The run block of the job's only step, dedented. Empty output means the workflow moved on.
awk '
  /^  record-verified:/ { job = 1 }
  job && /^        run: \|$/ { body = 1; next }
  body { if ($0 ~ /^          / || $0 ~ /^[[:space:]]*$/) { sub(/^          /, ""); print; next } exit }
' "$WORKFLOW" > "$T/step.sh"
grep -q 'on_main' "$T/step.sh" || { echo 'record-verified.test.sh: run block not found in lint.yml'; exit 1; }

mkdir "$T/bin"
cat > "$T/bin/gh" <<'EOF'
#!/usr/bin/env bash
# Fake gh. $STATE: main.list (main history, oldest first), off-main (commits that exist but are not
# on main), ref (current record commit), records/<commit> (the sha a record holds), ops, tree.json,
# commit.json. API paths matching $FAIL_ON answer 502; unknown commits answer 404 like gh does.
S="$STATE" method=GET path='' fields=()
while [ $# -gt 0 ]; do
  case "$1" in
    -X) method="$2"; shift ;;
    -H|--jq|--input) shift ;;
    -f|-F) fields+=("$2"); shift ;;
    repos/*) path="$1" ;;
  esac
  shift
done
if [ -n "${FAIL_ON-}" ] && [[ "$path" =~ $FAIL_ON ]]; then
  echo '{"message":"Server Error"}'; echo 'gh: Server Error (HTTP 502)' >&2; exit 1
fi
not_found() { echo '{"message":"Not Found","status":"404"}'; echo 'gh: Not Found (HTTP 404)' >&2; exit 1; }
pos() { grep -nx "$1" "$S/main.list" | cut -d: -f1; }
set_ref() { local f; for f in "${fields[@]}"; do [[ "$f" == sha=* ]] && echo "${f#sha=}" > "$S/ref"; done; }
case "$path" in
  repos/*/compare/*)
    spec="${path#*/compare/}" base="${spec%%...*}" head="${spec#*...}"
    [ "$head" = main ] && head="$(tail -n 1 "$S/main.list")"
    [ "$base" = "$head" ] && { echo identical; exit 0; }
    b="$(pos "$base")" h="$(pos "$head")"
    if [ -n "$b" ] && [ -n "$h" ]; then
      if [ "$h" -gt "$b" ]; then echo ahead; else echo behind; fi
      exit 0
    fi
    for c in "$base" "$head"; do [ -n "$(pos "$c")" ] || grep -qx "$c" "$S/off-main" || not_found; done
    echo diverged ;;
  repos/*/git/matching-refs/heads/ci/verified) if [ -f "$S/ref" ]; then cat "$S/ref"; fi ;;
  repos/*/contents/main-sha*) cat "$S/records/${path#*ref=}" ;;
  repos/*/git/trees) cat > "$S/tree.json"; echo tree1 ;;
  repos/*/git/commits)
    cat > "$S/commit.json"
    c="rec$(($(ls "$S/records" | wc -l) + 1))"
    jq -r '.tree[0].content' "$S/tree.json" > "$S/records/$c"
    echo "$c" ;;
  repos/*/git/refs/heads/ci/verified) if [ "$method" = PATCH ]; then set_ref; echo PATCH >> "$S/ops"; fi ;;
  repos/*/git/refs) set_ref; echo CREATE >> "$S/ops" ;;
  *) echo "fake gh: unhandled $path" >&2; exit 99 ;;
esac
EOF
chmod +x "$T/bin/gh"

# check <desc> <main history> <off-main commits> <recorded sha|-> <SHA> <502 path regex|->
#       <ok|fails> <ops: CREATE|PATCH|none> <record after|-> <new record's parent|-|none>
check() {
  local desc="$1" main="$2" offmain="$3" recorded="$4" sha="$5" failon="$6"
  local want_rc="$7" want_ops="$8" want_record="$9" want_parent="${10}"
  local S out rc ops record=- parent=- ok=1
  S="$(mktemp -d "$T/s.XXXXXX")"; mkdir "$S/records"; : > "$S/ops"; mkdir -p "$S/tmp"
  tr ' ' '\n' <<<"$main" > "$S/main.list"; tr ' ' '\n' <<<"$offmain" > "$S/off-main"
  if [ "$recorded" != - ]; then echo rec1 > "$S/ref"; echo "$recorded" > "$S/records/rec1"; fi
  [ "$failon" = - ] && failon=''
  out="$(STATE="$S" FAIL_ON="$failon" REPO=o/r SHA="$sha" RUNNER_TEMP="$S/tmp" PATH="$T/bin:$PATH" \
    bash "$T/step.sh" 2>&1)"; rc=$?
  ops="$(tr '\n' ' ' < "$S/ops" | sed 's/ $//')"; [ -n "$ops" ] || ops=none
  [ -f "$S/ref" ] && record="$(cat "$S/records/$(cat "$S/ref")")"
  [ -f "$S/commit.json" ] && parent="$(jq -r '.parents[0] // "none"' "$S/commit.json")"
  if [ "$want_rc" = ok ]; then [ "$rc" -eq 0 ] || ok=0; else [ "$rc" -ne 0 ] || ok=0; fi
  [ "$ops" = "$want_ops" ] && [ "$record" = "$want_record" ] && [ "$parent" = "$want_parent" ] || ok=0
  # a record commit carries only main-sha — never workflow files (GITHUB_TOKEN could not push those)
  if [ -f "$S/tree.json" ] && ! jq -e '[.tree[].path] == ["main-sha"]' "$S/tree.json" >/dev/null; then ok=0; fi
  if [ "$ok" = 1 ]; then
    pass=$((pass+1))
  else
    fail=$((fail+1))
    printf '✗ %s (rc=%s ops=%s record=%s parent=%s)\n    %s\n' "$desc" "$rc" "$ops" "$record" "$parent" "${out//$'\n'/$'\n'    }"
  fi
}

check 'first record: no ref yet -> create a root record'          'm1 m2'    ''    -    m2 - ok CREATE m2 none
check 'main moved on -> new record on top of the old one'          'm1 m2 m3' ''    m1   m3 - ok PATCH  m3 rec1
check 'sha already recorded -> nothing to do'                      'm1 m2'    ''    m2   m2 - ok none   m2 -
check 'an older run finishing late never moves the record back'    'm1 m2 m3' ''    m3   m2 - ok none   m3 -
check 'a sha a rewrite removed from main (diverged) is not recorded' 'm1 m2'  'x'   m1   x  - ok none   m1 -
check 'a sha GitHub no longer has (404) is not recorded'           'm1 m2'    ''    m1   y  - ok none   m1 -
check 'a recorded sha a rewrite removed from main is replaced'     'n1 n2'    'xold' xold n2 - ok PATCH n2 rec1
check 'main rewound below the record -> record the current tip'    'm1 m2'    'm3'  m3   m2 - ok PATCH  m2 rec1
check 'API error on "is this sha on main" fails the job'           'm1 m2 m3' ''    m1   m3 'compare/m3\.\.\.main' fails none m1 -
check 'API error on "is the record on main" fails the job'         'm1 m2 m3' ''    m3   m2 'compare/m3\.\.\.main' fails none m3 -
check 'API error on "which is newer" fails the job'                'm1 m2 m3' ''    m3   m2 'compare/m2\.\.\.m3'   fails none m3 -

printf 'record-verified.test.sh: %d passed, %d failed\n' "$pass" "$fail"
[ "$fail" -eq 0 ]
