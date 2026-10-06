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

By default, reports go to `colrep/<Collection>_<YYYY-MM-DD>/` next to the script
(`<Collection>.json` + `<Collection>.md`). Re-running on the same day overwrites them.
`--out` writes to the given directory as-is. `colrep/` is not tracked by git.

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

## Tests

```bash
python3 -m unittest discover -s tests
```
