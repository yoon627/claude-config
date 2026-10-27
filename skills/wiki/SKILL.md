---
name: wiki
description: An ingest/query/lint orchestration that operates the persistent project memory (LLM Wiki). Two layers — the current repo's `wiki/` (that repo's decisions and lessons) and the shared `~/.claude/wiki/` (publishable facts useful to several repos and lessons about global assets). It accumulates raw sources and working knowledge as interlinked markdown pages (ingest), answers from the accumulated pages (query) and checks their integrity (lint). Use on an explicit `/wiki <ingest|query|lint>` call. Not for simple questions or code changes (those belong to dlc or direct work).
---

# wiki — operating the LLM Wiki (persistent project memory)

The wiki has two layers (CLAUDE.md §11 is the single source of the placement rules):
- **repo wiki** `<ROOT>/wiki/` — that repo's decisions and lessons. Its operating conventions are that wiki's `WIKI.md`.
- **shared wiki** `~/.claude/wiki/` — publishable facts useful to several repos and decisions and lessons about global assets. Its conventions are `~/.claude/wiki/WIKI.md`. It is a private GitHub repo cloned separately at this path (`~/.claude` does not track it). The repository is private, but every repo session reads it and copies from it, so it holds only content that passed the "Public check" below.

**Current repo check**: if `[ "$(git rev-parse --path-format=absolute --git-common-dir)" -ef "$HOME/.claude/.git" ]` is true, it is `~/.claude` (worktrees included; with `-ef` it does not depend on notation differences such as `C:/`·`/c/` or symbolic links) — the two layers are the same, and the place to read and write is the absolute path `~/.claude/wiki`. Worktrees have no copy, so writes happen only in a main session. `rg`·Grep run from the `~/.claude` root skip this folder because of the parent `.gitignore`, so name the path when searching. If it is false, it is "another repo" (non-git directories included). Do not judge it with `git -C ~/.claude …` (the worktree isolation guard refuses it).

At the start, **always read the target wiki's `WIKI.md`**. This skill is the execution procedure that enforces those conventions. Which wiki it goes to is set by §11, the page format by the target wiki's WIKI.md. Page writes are done **only by the main agent** (single-writer, the same principle as `plans/`). On conflict, CLAUDE.md wins.

## When to use
- An explicit `/wiki ingest|query|lint` call.
- dlc integration (CLAUDE.md §11): at the start of work, look up both wikis (only those that exist — `wiki_search.py`, query step 1); after the work, judge the target layer of reusable knowledge and propose ingest (not automatic).
- Not for code changes or simple questions.

## Arguments
| Input | Action |
|---|---|
| `ingest <path\|description>` | raw/knowledge → update pages of the target wiki + index/log |
| `query <question>` | search both wikis, read the pages and answer; file it if worthwhile |
| `lint` | check and report the integrity of the current repo's wiki |
| (no argument) | summary of both `index.md` files + usage |

Branch on the first token. For an unknown subcommand, print the usage and stop.

## Public check (everything that a shared-wiki entry publishes)
The shared wiki is a private repo, but every repo session reads it and copies from it into public repos — history that was copied and pushed is not erased by a revert. The forbidden list and the surfaces to check (pages·`sources`·index·log·`source/` summaries·plans·branch/worktree names·commit messages·PR titles/bodies) are defined only in **CLAUDE.md §11** — tokens, keys and PII are always forbidden.
- Put only publicly verifiable evidence (official doc URLs·public issues·reproductions without private code) in `sources`. Do not carry private code paths over as evidence.
- If the source of a proposal is `private` or **no source is written** (unknown = treated as private), show the final diff before committing and confirm with `AskUserQuestion` (in chat where it is unavailable) (CLAUDE.md §1 publicly visible).
- If it fails the check, take it out of the shared wiki and send it to the source repo's wiki.

## ingest
1. **Target layer judgment** (§11): unique to the repo → repo wiki / publishable facts useful to several repos or lessons about global assets → shared / not a target (reason). If unsure, the repo wiki. If the target is the repo wiki but there is no repo wiki or the directory is not a git repo, not a target + reason (a shared-wiki target is still proposed in step 2).
2. **A shared-wiki target in another repo** is not written: leave `in a ~/.claude main session: /wiki ingest <summary · public evidence · source (public/private)>` in the Report and in the source plan's log `# Deferred` (the Report only without a plan) and stop (the same format as §11). Write only `public`/`private` in the source field (do not write private repo names). The summary and evidence must be sentences that already passed the public check above.
3. When writing to the shared wiki, write directly into `~/.claude/wiki` in a main session and commit to that repo's main (the CLAUDE.md §3-1·§8 exception — worktrees have no copy). In a worktree session, do not write; leave it in the plan log `# Deferred` and do it in a main session. Push only on request. Another repo's repo wiki is written by that repo's rules.
4. Read the target wiki's `WIKI.md` (check the conventions).
5. If an original is given, keep it in the target wiki's `raw/` (mkdir if absent) (once, immutable afterwards — never edited or deleted) → check that it is ignored with `git check-ignore <wiki>/raw/<f>`. Raw is loaded only from user curation or ingest input. Raw placed in a worktree is gitignored and is deleted without warning when the worktree is cleaned up — if it must be kept, move it before the cleanup.
6. If based on an original, create a 1:1 summary `pages/source/<name>.md` (for the shared wiki, the public check — a summary of a private original does not go in the shared wiki).
7. Update or create the related `entity` (external facts·versions)/`decision` (decisions·lessons)/`concept` pages. One ingest touches several pages. If the same fact already exists, update it instead of making a new page.
8. Each page meets the rules: frontmatter, ≥2 outbound `[[links]]` (only to pages in the same wiki — a reference across layers is the path text `~/.claude/wiki/pages/<cat>/<stem>.md`), sources, contradictions as `> [!conflict]`. **Before loading raw or writing a page, check for tokens/keys/PII → mask or stop if found** (no proceeding after a warning); for the shared wiki, the public check too.
9. Register in `index.md` + append to `log.md` (`## [YYYY-MM-DD] ingest | <title>`).
10. Check with `check_links.py` (links·index) and `wiki_check.py schema` (frontmatter format), then report (the commands are in the lint section). If you changed a page with `covers`, also run `wiki_check.py stale --report` (carrying the value over is in the Freshness section). For a wiki with `[smoke]` in its config, also run `wiki_check.py smoke`. For a shared-wiki entry, run the public check once more before committing (diff confirmation for a private source).

## query
1. Find the related pages with `uv run --no-project python "${CLAUDE_SKILL_DIR}/wiki_search.py" <query terms…>` and read them.
   - The shared wiki (`CLAUDE_SHARED_WIKI`, otherwise `~/.claude/wiki`) is found regardless of cwd, and the repo wiki is found by walking up from the current directory to the repo root; both are searched together. If both are the same path, it is found once.
   - Each result shows the layer (`[공용]` (shared)/`[repo]`), the absolute path, the index summary and the matching body lines.
     - A matching line carries its section and line range (`L20 §결정 (L18-35): …`). To read only the section, give that range to Read's offset·limit.
     - Each result carries the related pages linked within the same wiki (`관련: → 나가는 · ← 들어오는`, i.e. related: outgoing · incoming). Aliases `[[a|b]]` count as links too, and links in index.md do not count as incoming.
   - `--limit N` (default 5)·`--category C` may go anywhere before or after the query terms. For a word starting with `-` (a flag name), drop the leading `-`.
   - Structural queries (used instead of query terms):
     - `--links-to <stem>`: prints every line containing a link to that page (once even if a line has several). Use it to find the affected pages before changing a decision.
     - `--open`: prints every unresolved `[!open]`·`[!conflict]`.
     - Both print, per page, `L<line> §<section>: …` records under a header line (layer·name·absolute path). They do not follow `--limit`.
     - `--category` applies only to the pointing pages (the ones holding the callout).
   - The first line lists the wikis found and their page counts; use it to confirm where it searched. If the default path has no shared wiki, it searches only the repo wiki, with a warning on stderr.
   - On exit 1 (no results) or results that miss, search again with other words (English identifiers·synonyms) and scan both `index.md` files directly (the shared one is `~/.claude/wiki/index.md`). A single Hangul syllable (`훅`) is not found.
   - Exit 2 cases:
     - There is no wiki, word, category or stem to search.
     - A query mode was used together with query terms or with another mode.
     - `CLAUDE_SHARED_WIKI` is not a wiki.
     - A read error.
     - The reader of stdout closed first, so the output could not be written to the end (if `| head` closes after receiving everything, there is no error and the exit code is the usual one).
     - An unexpected error (traceback on stderr).
   - On exit 2, read the reason on stderr, fix the query or settings and search again — skip the lookup only for `찾을 wiki 가 없다` (no wiki to search).
   - The score is the idf-weighted sum of stem·title match 3, index summary match 2.5 and body BM25 (capped at 2.2). Hangul is split into 2-grams, so it matches even with particles attached.
2. Answer from the pages (not raw chunks). Cite the evidence pages **together with which wiki they belong to**.
3. If it has reuse value, file it in **the current repo's wiki** as `pages/query/<slug>.md` (frontmatter+links) + append to that wiki's `log.md`. If an answer based on shared pages is worth filing from another repo, route it to the shared-wiki proposal of ingest step 2. Shared pages do not point to pages of private repos.
4. If there are no related pages, state "not in the wiki" (no guessing). Propose ingest if needed.

## lint
Only the current repo's wiki (in `~/.claude`, the shared wiki — pass `~/.claude/wiki` as the path to the check commands). Checks only, no automatic fixes (fixes after the report and user approval). Check items:
- dead `[[links]]` (target missing) / orphans (no page other than `index.md` points to them, inbound=0) / outbound links <2.
- `index.md` ↔ `pages/**` mismatch (missing·extra).
- frontmatter format (required keys·category·dates etc.) and stem format·duplicates.
- covers freshness — pages whose `verified_at` differs from the current fingerprint of the covers files (Freshness section).
- representative questions — for each question the wiki must answer, is there a page to answer it, an index entry and body evidence; were no traces of in-progress work (branch names·plan status·point-in-time tallies) left in pages (only wikis with `[smoke]` in their config).
- candidates for contradictions (unresolved `[!conflict]`)·stale entity versions (outdated versions of external facts — different from `wiki_check.py stale`). For the shared wiki, public check violation candidates too.

Mechanical checks are done by the scripts below (stdlib only); semantic checks (contradictions·stale entity versions·public check) by the LLM.
- `check_links.py` — dead links·orphans·outbound<2·index sync: `uv run --no-project python "${CLAUDE_SKILL_DIR}/check_links.py" [wiki path]` (without an argument, the current repo's wiki). Aliases `[[a|b]]` count as links to `a`. But index registration accepts only `[[a]]` without an alias (the same standard as smoke). exit 0 clean, 1 violations — a page or index that is not UTF-8 gets a `UTF-8 아님` (not UTF-8) violation and the rest is still judged (for pages, the same verdict as schema), 2 no pages directory or a read failure (permissions·subdirectories — no violation list, `check_links: 읽기 실패 — <path>: <reason>`, a read failure).
- `wiki_check.py schema` — frontmatter format: `uv run --no-project python "${CLAUDE_SKILL_DIR}/wiki_check.py" schema [wiki path] [--config file]`.
  - Without a wiki path, it walks up from the current directory to the repo root looking for `wiki/`. For a wiki elsewhere, such as `docs/wiki`, pass the path.
  - exit 0 pass, 1 violations (one `<path>: <rule> — <detail>` line each; the path is relative to the repo root, or to the wiki's parent outside a repo), 2 usage·config·environment error.
  - In a value, as in YAML, everything from a `#` after whitespace is a comment. `[PR #82, …]` is a violation even if closed on that line, since only `[PR` remains. If the `#` is part of an item, quote that item (`["PR #82", …]`); if it is a note, move it to a comment after the `]` (`[a.kt]  # note`). The same goes for a note attached after `[ … ]`. If the note is quoted too, covers becomes a pattern that matches nothing and stale silently misses it.
  - Adapt the rules to that wiki's WIKI.md conventions with `<wiki>/wiki-check.toml`. The template is `templates/wiki-check.toml`, and the key descriptions are in the template's comments. Without a config, it runs on the shared WIKI.md conventions (5 required keys, 5 categories, `created`·`updated` dates). WIKI.md is canonical for the format, so if the two disagree, fix the config.
  - Reading a config needs Python 3.11+ (`tomllib`). On 3.9·3.10 only the checks without a config run.
- `wiki_check.py stale --report` — covers freshness: `uv run --no-project python "${CLAUDE_SKILL_DIR}/wiki_check.py" stale --report [wiki path]`. It does not use config values for its judgment, but if a config exists, it reads and validates it (config errors below). If there are no pages with `covers`·`verified_at` and no unreadable pages (not UTF-8·frontmatter not closed·a covers value or item that starts with `[` but does not end with `]`), it prints "검사 대상 아님" (nothing to check) and exits 0, so it is safe to run on every wiki. An unreadable page is a "covers 읽기 실패" (covers read failure) violation (exit 1) even without covers. If there are covers pages, run it inside a git repo. The judgment and exit codes are in the Freshness section.
- `wiki_check.py smoke` — representative questions: `uv run --no-project python "${CLAUDE_SKILL_DIR}/wiki_check.py" smoke [wiki path] [--config file]`. Without `[smoke]` in the config, it prints "검사 대상 아님" and exits 0, so it is safe to run on every wiki. With `[smoke]` but no check filled in, exit 2. Examples are in the template's comments.
  - For each `[[smoke.questions]]`, it passes when `page` (a `.md` path relative to pages) exists, `index.md` has `[[stem]]`, and some line of the body (after the frontmatter) matches `expect`. `expect` is a Python `re` searched line by line like grep. POSIX character classes (`[[:space:]]`) and GNU grep dialects (`\<`·`\>`, `[=…=]`·`[.….]` inside a character set) are read differently by Python `re`, so they are blocked with exit 2 — use `\s`·`[0-9]`·`\b`. The same goes for `[smoke.forbid] patterns`.
  - `[smoke.forbid]` looks at the full text of the pages' `.md` files (frontmatter included) line by line and reports matching lines as FAIL. `branch_names` (whole lowercase names that contain a hyphen and no `/`, after removing the remote name from local and remote-tracking branch names — names containing `/` such as `feat/x-y` are not checked. The remote name is read as one level, so branches of a remote whose name contains `/`, such as `team/fork`, are not checked. It must run inside a git repo; outside a repo, no other check runs either and the whole smoke exits 2), `plan_status` (`status: in_progress`), `patterns` (a list of regular expressions); all are off by default. A sentence that copied in-progress state becomes a wrong fact once that work ends.
  - exit 0 pass, 1 failure (one `PASS | …`·`FAIL | …` line each plus a total), 2 usage·config·environment error.
- `wiki_check.py schema` is canonical for the frontmatter judgment. The frontmatter line of `check_links.py` is for compatibility, so it treats pages with a BOM and pages without a closing `---` differently. Running `check_links.py` alone does not catch duplicate pages with the same stem (one silently overwrites the other).
- If a config (`<wiki>/wiki-check.toml`) exists, schema·stale·smoke all read and validate the whole file. Unknown keys·wrong types·`[smoke]` regex errors (POSIX character classes included) make every command exit 2 in whatever section they are, and the hook reads the config only when there are covers pages and reports the error as a `systemMessage` every turn instead of the stale judgment. A single smoke typo also blocks the schema check of ingest step 10, so after fixing the config, run `schema` first.

Classify the results and report + propose fixes + append to `log.md` (`## [YYYY-MM-DD] lint | <summary>`).

## Freshness (`covers`·`verified_at`)
This section is canonical for the meaning, recommendations and judgment of the two keys. If a page that makes claims about code lists that code's paths in `covers`, `wiki_check.py stale` finds the cases where the code changed but the page stayed the same. Both keys are optional, and stale does not look at pages without them.

**`covers`** — a list of path patterns (inline `[a, b]` or block `- a`). An inline list must close on one line — if a value or block item starts with `[` but does not end with `]` (a multi-line list, cut off by a comment, characters after `[ … ]`), it is a schema violation and stale treats it as "covers 읽기 실패".
- Patterns are fnmatch on paths relative to the git top level. They are case-sensitive and `*` crosses `/` (`src/*` also matches `src/a/b.py` — it is not gitignore-style `**`). A pattern identical to the path always matches even if it contains `[`·`?`·`*`. The whole pattern is matched once reading `[…]` as a character set and once reading every `[` literally (`app/[id]/*` matches `app/[id]/page.tsx`). To mix a literal `[` and a character set in one pattern, write the literal one as `[[]` (`app/[[]id]/[ab].py`). An item that is empty, starts with `/`·`./`·`../`, ends with `/` or contains `\` is reported by schema as a violation.
- What to list (a recommendation — the script does not enforce it): only paths directly tied to claims whose truth changes when the code changes. The evidence is a measurement in one repo — broad covers hit about a third of the commits, and the confirmation became a formality.
- For the form, exact file paths, `dir/*` and `dir/*.ext` are recommended. These are forms that can be carried over to the `paths:` of `.claude/rules` (glob — `*` matches only within one directory and `**` crosses directories). Patterns whose `?`·`[...]` match `/` and patterns with several `*` cannot be moved as they are.

**`verified_at`** — the fingerprint of the covers files' contents at the time the page was checked against the code. `fp1-` followed by 16 lowercase hex characters.
- The fingerprint is a hash of, for each file in covers (wiki pages excluded), "the (mode, blob) that `git add -A` would record in the index now". It does not look at history, so regardless of fixup·rebase·squash·revert·shallow clones it is decided by one thing: "are the contents now the same as the checked contents". It changes even when only the executable bit changes, or when changing the covers list changes the file set.
- There is no separate command that makes the value. `stale --report` shows the current value per page. Write that value only after checking the page's claims against the covered files and fixing them, and name the checked files in the commit message that changes the value. Carrying one line of value over clears both the hook and the report, so no tool can stop it from being carried over without a check — this order is the only safeguard.
- Judgment: if the value equals the current fingerprint, OK; if it differs, STALE (a violation). Without a value, "미확인" (unconfirmed, not a violation). 7–64 hex characters are the old format (a commit value) and a violation — check the page again and replace it with the value the report shows. A version unknown to the script, such as `fp2-`, needs a script update (exit 2). `verified_at` without covers, or covers matching 0 files, is a violation.

**Modes** — `uv run --no-project python "${CLAUDE_SKILL_DIR}/wiki_check.py" stale <mode> [wiki path] [--config file]`

| Mode | Judgment | Use |
|---|---|---|
| `--report` | compares `verified_at` with the working-tree fingerprint per page. Does not look at history | audit·lint·CI |
| `--branch [--base REF]` | covers files changed in the commits of `merge-base(HEAD, base)..HEAD` but the page did not | CI·before push |
| `--stop-hook` | the same judgment as `--branch`, widened to the working tree (untracked included) | Claude Code Stop hook |

- `--branch`·`--stop-hook` do not look at order — once the page was changed on the branch, later covers changes are not reported either. Changes after the check are caught by `--report`, but only for pages with `verified_at`.
- The base is decided in this order: `--base`, config `[stale] base`, the default branch candidates (the fork point of HEAD with those of `origin/HEAD`·`origin/main`·`origin/master`·`main`·`master` that are not the current branch). CI passes it like `--base origin/$GITHUB_BASE_REF`. `--report` does not take `--base` (exit 2).
- `--branch`·`--report` read pages and config from the working tree. If there are uncommitted changes, they write "작업 트리 기준 — … 미커밋 변경 N개" (working-tree based — N uncommitted changes) at the top of the output and on stderr. CI judges by the committed contents.
- exit: 0 pass, 1 violations (one `<path>: …` line each), 2 usage·config·environment error (outside a repo, git failure, the base could not be decided, a fingerprint version unknown to the script). A page that is not UTF-8, whose frontmatter is not closed, or whose covers value or item starts with `[` but does not end with `]` has unknown covers and is a "covers 읽기 실패" violation. If there are no covers pages (for `--report`, `verified_at` pages too) and no unreadable pages, it prints "검사 대상 아님" and exits 0.

**CI conditions and limits of `--report`**
- For a value written in an uncommitted state to equal the CI value, commit the checked working tree as it is — no partial staging, no pre-commit formatter changing files, and commit or ignore the untracked files listed in covers.
- If CI has untracked artifacts listed in covers, STALE appears only in CI and does not clear on re-checking — ignore the artifacts or run on a clean checkout.
- Cases where the fingerprint differs between machines: before the renormalize commit after changing the line-ending rules in `.gitattributes`, two tracked paths differing only in case (case-insensitive file systems — the macOS·Windows default — vs Linux), ignore rules that differ per machine (`core.excludesFile`·`.git/info/exclude` — the untracked set changes).
- The fingerprint is computed through git's add path, so clean filters such as LFS run for each changed covers file — slow on large files, and it does not stop what the filter itself writes. `core.fsmonitor` also runs as in a normal `git status`. If set up as a hook, it is also called on git calls against the copy (update-index·ls-files). If `true` (the built-in daemon), status starts the daemon and creates `$GIT_DIR/fsmonitor--daemon*`. Apart from that, the only thing the tool writes is an index copy in a temporary directory — the copy is not written as a split index and does not call hooks in `core.hooksPath` (`post-index-change` etc.), and the real index·shared index·objects stay as they are.
- submodule gitlink changes: `git add` does not follow `diff.ignoreSubmodules`, so neither does the fingerprint. HEAD moves of a submodule with `submodule.<name>.ignore = all` are not in the fingerprint. The fingerprint follows the effective value where `.git/config` overrides `.gitmodules`. `git add -A` of git 2.54.0 follows only the `.gitmodules` value. So if this value is only in `.gitmodules`, the two agree. If `.git/config` changes whether it is `all` (putting `all` only in `.git/config`, or overriding `all` in `.gitmodules` with `none`), the fingerprint differs after the commit either way. `git add` before 2.54 does not follow this setting (2.54.0 release notes), so the `.gitmodules` side disagrees too.

**Clearing the notice** — the hook keeps no state, so it notifies again at the end of every turn until cleared.
1. Check the page's claims against the covered files and fix them. If there is `verified_at`, carry the value over after the check too.
2. If the change is unrelated to the claims, narrow covers. If there is `verified_at`, the file set changes and so does the fingerprint, so write the value again.
3. To turn the hook off in this repo, put `[stale] stop_hook = false` in `<wiki>/wiki-check.toml` (when a global registration overlaps a repo with its own gate). It does not affect `--branch`·`--report`.

**Registering the hook** — this skill does not register hooks or CI. Rules to follow when registering:
- The script path must exist on every machine that uses those settings. If it does not, python exits 2, and a Stop hook's exit 2 blocks every stop. Abbreviating the flag (`--st`·`--stop-h`) or attaching a value (`--stop-hook=…`) does not exit 2 (so stopping is not blocked), but it judges nothing and only emits an "인자 오류" (argument error) `systemMessage` every turn. Write `--stop-hook` as is in the registration command.
- The starting point is the `cwd` of the hook input JSON (once a worktree is entered, that worktree), and relative wiki paths·`--config` are relative to that repo root. Do not use `${CLAUDE_PROJECT_DIR}` in the wiki path — it stays at the session's start location, so a judgment inside a worktree looks at the main checkout's wiki. For locations that are not discovered, such as `docs/wiki`, pass the path. But do not pass the wiki path·`--config` when registering globally (`~/.claude/settings.json`); pass them only when registering in that repo's project settings. If passed globally, every repo without that path gets a `systemMessage` every turn (for `--config`, in repos with covers pages). And it cannot be turned off, because the `stop_hook = false` that turns it off would have to go in that missing wiki·config.
- The output is one of: none, `additionalContext`, `systemMessage`, always with exit 0. When stale and a tool·environment failure (the base could not be decided, unreadable pages when there are covers pages) coincide, one JSON carries both `hookSpecificOutput` and `systemMessage`. With nothing to do, there is no output (`stop_hook_active`, waiting for subagent·workflow background work, outside a repo, no wiki found by discovery, 0 covers pages, `stop_hook = false` etc.). If a wiki path passed as an argument does not exist, it reports that with `systemMessage`. When stale, it puts the pages to update·the covered files·how to clear it in `hookSpecificOutput.additionalContext` within 10,000 characters. Tool·environment failures (argument·stdin·config errors, git failure, the base could not be decided, unreadable pages (when there are covers pages — otherwise no output), exceeding 15 seconds) are reported with `systemMessage` ("wiki_check stale: …") — ending with no output would hide a gate that turned off. `additionalContext` is a format documented since Claude Code 2.1.163.
- On the default branch of a repo without a remote, and on an unborn HEAD, only the working tree is looked at (no warning).

**Python** — schema·stale (all three modes) without a config run from 3.9. With a config, 3.11+ (`tomllib`) is needed — on 3.9·3.10 the other modes (all but `--stop-hook`) exit 2 and the hook reports the version with `systemMessage`. So the features that need a config (rule tuning, `stop_hook = false`, smoke) are 3.11+. On Windows, it was confirmed on Windows 11·CPython 3.13·3.9 with the tests and a pipe-connected hook (python·`uv run`·Node parent) (2026-10-01). However, the paths covered by the tests skipped on Windows — git call time limits·cleanup of processes git started·the hook time budget (a fake git as an sh script), whether the `--report` fingerprint equals `git add -A` in various index states (conflicts·intent-to-add·non-UTF-8 paths·typechange·directory↔file switches) (they use symlinks and file names Windows cannot use), that the fingerprint computation does not call git hooks, process group signals, a hook started with standard stream fds closed, symlink wiki discovery·executable bits·pty·read permissions·`*` file names — were not confirmed on Windows. Console output was only checked to finish without exceptions in a new console, and it was not registered and run in Claude Code.

## Boundaries
- Page writes only by the main agent. `raw/` originals are never edited or deleted after loading (immutable).
- Sessions of other repos do not write to the shared wiki (proposals only). Every write to the shared wiki must pass the public check.
- No automatic fixes (lint stops at reporting). No unsupported assertions and no speculative pages (CLAUDE.md §1).
- Not a code change — separate from dlc. Even if the current repo has no wiki, look up the shared wiki (writing is not a target + reason).
