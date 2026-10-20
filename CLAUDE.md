# CLAUDE.md

## Coding rules

### 1. Think before coding
- State your assumptions. If something is unclear, ask instead of guessing.
- If there are several readings of a request, name them; don't silently pick one.
- Push back when a simpler approach exists.

### 2. Simplicity first
- Write the minimum code that solves the problem. No speculative features, options or abstractions.
- If 200 lines could be 50, rewrite it.

### 3. Surgical changes
- Touch only what the task requires. Match the existing style.
- Don't refactor, reformat or "improve" adjacent code. Clean up only what your own change made obsolete.

### 4. Goal-driven execution
- Turn each task into a checkable success criterion (ideally a test) before implementing.
- Loop until it is verified: `python3 -m unittest discover -s tests`.

## Questions on an Exported Collection: quotes only

When I ask about the **content** of an Exported Collection (see `GLOSSARY.md`), answer with quotes only.

- **Source**: the latest-dated export `colrep/<Collection>_<YYYY-MM-DD>/` unless I name another. If no export exists, say so and offer to run `python zotero_report.py --collection "<Collection>"`; don't export unasked.
- **Quotable**: highlight and underline text, and abstract sentences, verbatim. My own comments and notes only if labelled as mine (`💬 your comment:` / `📝 your note:`).
- **Format**: each quote as a blockquote followed by one source line, e.g.
  ```
  > PIOTs represent a mass balanced map of biophysical flows ...
  — Wieland et al. 2022, p. 684
  ```
  (no page for abstract quotes: `— Wieland et al. 2022, abstract`). No other text: no intro, summary, interpretation or conclusion.
- **No match**: reply exactly `No matching quotes in <Collection> export.` Don't offer near-misses.
- **Not covered**: counts and metadata questions (e.g. "how many highlights?", "which items lack annotations?") get a plain answer from `stats` / item metadata.
- **Override**: an explicit "summarize", "explain", "compare" etc. lifts the rule for that one question only.

## Project pointers
- Exports live in `colrep/` (untracked); usage, DB location and output format are in `README.md`.
- Tests: `python3 -m unittest discover -s tests`.
