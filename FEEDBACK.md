# Global feedback

Corrections the user made to how Claude works, applied in every repo's session (imported by `CLAUDE.md`; rules for saving and promoting them are in `CLAUDE.md` §12). One line per rule: an imperative rule — the short reason.

## Responses

- When asking for a confirmation or approval, summarize what changes in about 3 plain lines plus one example; show raw wording or jargon lists only when asked — a dozen bullets of copied rule text was unreadable, while 3 plain items were approved at once.

## Working

- Before saying a tool is missing or working around it, check with `which <tool>` / `<tool> --version` — an environment notice saying "not available" is a hypothesis; trusting it twice led to a false "cannot create the PR" ([[lesson-grep-absence-not-proof]]).
- Run verification commands with the session scratchpad as cwd, and before `rm`/overwrite check by creation time and content (`ls -la --time-style=full-iso`) that this work created the target; otherwise report it, do not delete — a common name in a shared path can be someone else's data ([[lesson-delete-only-what-you-created]]).
- When several small tasks are ff-merged into local main in a row, push main once when the series ends (or when asked), not after each one — every main push raises a permission prompt.
