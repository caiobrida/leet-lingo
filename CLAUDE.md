# leet-lingo

## Coding standards

### No comments

Code in this repo carries no comments — not in `/executor` (Python), not in `/api` (C#), not in `/web`. Names and structure carry the meaning; if a line needs a comment to be understood, rewrite the line.

Read literally: this includes Python docstrings and C# XML doc comments.

`/code-review` treats any comment introduced in changed code as a Standards finding.

### English in code

All code is written in English, across every project. This covers identifiers (variables, functions, classes, types), file and folder names, log and error message strings, and test names.

Domain terms follow the same rule: the glossary in `CONTEXT.md` records the English term (`verdict`, `submission`, `test case`, `harness`), and code uses it exactly as recorded.

### Git attribution

Commits, branch names, PR titles and PR bodies in this repo carry no agent attribution. Never add a `Co-Authored-By:` trailer naming an AI, a "Generated with" footer, or any comparable marker. The history reads as authored by the repo owner alone.

## Agent skills

### Issue tracker

Issues and specs live as local markdown files under `.scratch/<feature-slug>/`. See `docs/agents/issue-tracker.md`.

### Triage labels

The five canonical triage roles, each label string equal to its name. See `docs/agents/triage-labels.md`.

### Domain docs

Single-context — `CONTEXT.md` and `docs/adr/` at the repo root. See `docs/agents/domain.md`.
