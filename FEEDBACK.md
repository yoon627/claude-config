# Global feedback

Corrections the user made to how Claude works, applied in every repo's session (imported by `CLAUDE.md`; rules for saving and promoting them are in `CLAUDE.md` §12). One line per rule: an imperative rule — the short reason.

## Responses

- When asking for a confirmation or approval, summarize what changes in about 3 plain lines plus one example; show raw wording or jargon lists only when asked — a dozen bullets of copied rule text was unreadable, while 3 plain items were approved at once.

## Working

- Before saying a tool is missing or working around it, check with `which <tool>` / `<tool> --version` — an environment notice saying "not available" is a hypothesis; trusting it twice led to a false "cannot create the PR" ([[lesson-grep-absence-not-proof]]).
- Run verification commands with the session scratchpad as cwd, and before `rm`/overwrite check by creation time and content (`ls -la --time-style=full-iso`) that this work created the target; otherwise report it, do not delete — a common name in a shared path can be someone else's data ([[lesson-delete-only-what-you-created]]).
- When several small tasks are ff-merged into local main in a row, push main once when the series ends (or when asked), not after each one — every main push raises a permission prompt.
- When `verify.sh` ends `ALL PASS (skip: <axis>)` and that axis covers the changed files (`.sh` → shellcheck, `.ps1` → PowerShell, `.zsh` → zsh), install the tool and run the axis, or send the unit through CI (`/e merge`) — do not local ff-merge on the skip; a shellcheck skip let a red main reach the next unit ([[lesson-skipped-axis-blocks-merge]]).
- For date, time zone, version or encoding logic, write the failing test first and check values by round trip, injecting the clock and time zone — format checks passed while the values were wrong ([[lesson-test-after-implementation]]).
- Make a test read the shipped file itself, not a copy of it, and assert a marker of the branch taken, not only the exit code — a copied artifact drifted from the real one and still passed ([[lesson-test-copies-artifact]]).
- Before starting non-trivial work, check open PRs, remote branches and other plans for the same change — two PRs built one feature twice and 553 lines were thrown away ([[lesson-parallel-duplicate-implementation]]).
- When a tool errors, compare its `--version` with the upstream changelog before working around it — the same bug was worked around six times though upstream had fixed it ([[lesson-stale-tool-version]]).
- Fix a failure mode by the signal that detects it, not by one repo's constants or labels — a fix hardcoded for one repo came back in another ([[lesson-fix-scoped-to-one-repo]]).
- Keep machine-specific absolute paths out of tracked config — paths flipping between machines left changes staged for days and stalled auto-pull ([[lesson-tracked-config-machine-paths]]).
- When mirroring an existing parser, mirror its preprocessing (CRLF, BOM) and its tolerances too, and build fixtures from the documented template — a partial mirror shipped two silent defects ([[lesson-parser-precedent-partial-mirror]]).
- Do not print output that may hold a secret on the strength of a filter; pick a command that does not emit it, or prove the filter removes it in the real format ([[lesson-verify-secret-redaction]]).
- When a script builds a deploy venv from a local project with `uv sync --no-editable`, pass `--reinstall-package <project>` — uv reuses the cached wheel of the same version and installs the old code.
