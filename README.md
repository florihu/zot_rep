Small rep for datafield extraction from zotero database including (A) basic item info (B) abstract (C) annotations (D) comments (E) notes.

## Usage

```bash
python zotero_report.py --list                                   # list collection names
python zotero_report.py --collection "pySUTO"                    # export a collection
python zotero_report.py --collection "pySUTO" --out ./reports    # custom output dir
python zotero_report.py --collection "pySUTO" --db /path/to/zotero.sqlite
```

## Database location

The database path is resolved in this order:

1. `--db /path/to/zotero.sqlite`
2. the `ZOTERO_DB` environment variable
3. auto-discovery: `~/Zotero/zotero.sqlite`, then `~/.zotero/zotero/zotero.sqlite`

If your Zotero data directory is elsewhere, set it once, e.g. in `~/.bashrc`:

```bash
export ZOTERO_DB=/path/to/Zotero/zotero.sqlite
```

Zotero may stay open; the database is copied to a temp file before reading.

## Output

By default, reports go to `rep/<Collection>/` next to the script
(`<Collection>.json` + `<Collection>.md`). Re-running overwrites them; `rep/` is
tracked by git, so earlier versions live in the git history (commit new exports
yourself). `--out` writes to the given directory as-is.

## Annotation stats

Each item and the collection as a whole get a `stats` object in the JSON:

| Field | Meaning |
| --- | --- |
| `annotations` | all annotations (highlights, underlines, sticky notes, images, ...) |
| `highlights` | annotations of type `highlight` |
| `underlines` | annotations of type `underline` |
| `comments` | annotations with a non-empty comment, any type |
| `avg_text_words` | average words of highlighted/underlined text (`null` if none) |
| `avg_comment_words` | average words of comments (`null` if none) |

Averages are rounded to 1 decimal. Collection averages are pooled over all
annotations. The Markdown shows the collection summary in the header and an
`**Annotations:**` line for each item that has annotations.

## Asking Claude about an export

`CLAUDE.md` sets up Claude Code for this repo. Questions about the content of an
exported collection are answered **with quotes only**: verbatim highlights,
underlines or abstract sentences from the `rep/` export, each followed
by a source line (`— Wieland et al. 2022, p. 684`). Your own comments and notes
are only quoted when labelled as yours.

- No match → `No matching quotes in <Collection> export.`
- Few quotes (< 3, or all from one paper), or you say `suggest papers` → up to 5
  further sources from the same export, each with one quoted abstract sentence.
- Count or metadata questions ("how many highlights?") get a plain answer.
- Say "summarize", "explain", "compare", ... to lift the rule for one question.

Terms (Collection, Export, Quote, Annotation, ...) are defined in `GLOSSARY.md`.

## Tests

```bash
python3 -m unittest discover -s tests
```
