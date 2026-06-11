#!/usr/bin/env python3
"""
zotero_report.py — Export a Zotero collection to structured JSON + human Markdown.

Pulls, per paper: metadata, abstract, PDF annotations (highlighted text + your
comments, with page + color + order), and standalone notes.

Reads ~/Zotero/zotero.sqlite directly. No add-on required. Zotero may stay open
(the DB is copied to a temp file first to avoid lock errors).

Usage:
    python zotero_report.py --list
    python zotero_report.py --collection "Copper PSUT"
    python zotero_report.py --collection "Copper PSUT" --out ./reports
    python zotero_report.py --collection "Copper PSUT" --db /path/to/zotero.sqlite
"""

import argparse
import json
import os
import re
import shutil
import sqlite3
import sys
import tempfile
from html import unescape
from pathlib import Path

# ----------------------------------------------------------------------------- helpers

ANNOTATION_TYPES = {1: "highlight", 2: "note", 3: "image", 4: "ink", 5: "underline"}


def default_db_path():
    candidates = [
        Path.home() / "Zotero" / "zotero.sqlite",
        Path.home() / ".zotero" / "zotero" / "zotero.sqlite",
    ]
    for c in candidates:
        if c.exists():
            return c
    return candidates[0]


def open_db(db_path):
    """Copy the DB to a temp file so we can read even while Zotero holds a lock."""
    db_path = Path(db_path).expanduser()
    if not db_path.exists():
        sys.exit(f"ERROR: Zotero DB not found at {db_path}. Pass --db explicitly.")
    tmp = Path(tempfile.gettempdir()) / "zotero_report_copy.sqlite"
    shutil.copy2(db_path, tmp)
    conn = sqlite3.connect(f"file:{tmp}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    return conn


def strip_html(s):
    if not s:
        return ""
    s = re.sub(r"<\s*br\s*/?>", "\n", s, flags=re.I)
    s = re.sub(r"</\s*p\s*>", "\n\n", s, flags=re.I)
    s = re.sub(r"<[^>]+>", "", s)
    return unescape(s).strip()


# ----------------------------------------------------------------------------- queries

def list_collections(conn):
    rows = conn.execute(
        "SELECT collectionName FROM collections ORDER BY collectionName"
    ).fetchall()
    return [r["collectionName"] for r in rows]


def resolve_collection_id(conn, name):
    row = conn.execute(
        "SELECT collectionID FROM collections WHERE collectionName = ?", (name,)
    ).fetchone()
    if not row:
        cols = list_collections(conn)
        sys.exit(
            f"ERROR: collection '{name}' not found.\nAvailable:\n  "
            + "\n  ".join(cols)
        )
    return row["collectionID"]


def items_in_collection(conn, collection_id):
    """Top-level items (not notes/attachments) in the collection."""
    q = """
        SELECT i.itemID, i.key, it.typeName
        FROM collectionItems ci
        JOIN items i               ON i.itemID = ci.itemID
        JOIN itemTypes it          ON it.itemTypeID = i.itemTypeID
        WHERE ci.collectionID = ?
          AND it.typeName NOT IN ('attachment', 'note', 'annotation')
        ORDER BY i.itemID
    """
    return conn.execute(q, (collection_id,)).fetchall()


def field_map(conn, item_id):
    q = """
        SELECT f.fieldName, idv.value
        FROM itemData idata
        JOIN fields f              ON f.fieldID = idata.fieldID
        JOIN itemDataValues idv    ON idv.valueID = idata.valueID
        WHERE idata.itemID = ?
    """
    return {r["fieldName"]: r["value"] for r in conn.execute(q, (item_id,)).fetchall()}


def creators(conn, item_id):
    q = """
        SELECT c.firstName, c.lastName, ct.creatorType
        FROM itemCreators ic
        JOIN creators c            ON c.creatorID = ic.creatorID
        JOIN creatorTypes ct       ON ct.creatorTypeID = ic.creatorTypeID
        WHERE ic.itemID = ?
        ORDER BY ic.orderIndex
    """
    out = []
    for r in conn.execute(q, (item_id,)).fetchall():
        name = " ".join(p for p in [r["firstName"], r["lastName"]] if p)
        out.append({"name": name.strip(), "type": r["creatorType"]})
    return out


def tags(conn, item_id):
    q = """
        SELECT t.name
        FROM itemTags itg
        JOIN tags t ON t.tagID = itg.tagID
        WHERE itg.itemID = ?
        ORDER BY t.name
    """
    return [r["name"] for r in conn.execute(q, (item_id,)).fetchall()]


def child_notes(conn, item_id):
    q = """
        SELECT n.note
        FROM itemNotes n
        WHERE n.parentItemID = ?
    """
    return [strip_html(r["note"]) for r in conn.execute(q, (item_id,)).fetchall()]


def annotations(conn, item_id):
    """Annotations live on attachment children of the item."""
    q = """
        SELECT a.type, a.text, a.comment, a.color, a.pageLabel, a.sortIndex
        FROM itemAttachments att
        JOIN itemAnnotations a ON a.parentItemID = att.itemID
        WHERE att.parentItemID = ?
        ORDER BY a.sortIndex
    """
    out = []
    for r in conn.execute(q, (item_id,)).fetchall():
        out.append(
            {
                "type": ANNOTATION_TYPES.get(r["type"], str(r["type"])),
                "highlighted_text": (r["text"] or "").strip(),
                "comment": (r["comment"] or "").strip(),
                "color": r["color"],
                "page": r["pageLabel"],
            }
        )
    return out


# ----------------------------------------------------------------------------- assembly

def build_record(conn, item_row):
    item_id = item_row["itemID"]
    fm = field_map(conn, item_id)
    return {
        "key": item_row["key"],
        "item_type": item_row["typeName"],
        "title": fm.get("title", "(untitled)"),
        "authors": creators(conn, item_id),
        "year": (fm.get("date") or "")[:4],
        "date": fm.get("date", ""),
        "publication": fm.get("publicationTitle")
        or fm.get("bookTitle")
        or fm.get("publisher", ""),
        "doi": fm.get("DOI", ""),
        "url": fm.get("url", ""),
        "abstract": fm.get("abstractNote", ""),
        "tags": tags(conn, item_id),
        "annotations": annotations(conn, item_id),
        "notes": child_notes(conn, item_id),
    }


def to_markdown(collection_name, records):
    L = [f"# Zotero Report — {collection_name}", ""]
    L.append(f"*{len(records)} item(s)*")
    L.append("")
    for rec in records:
        authors = "; ".join(a["name"] for a in rec["authors"]) or "—"
        L.append(f"## {rec['title']}")
        L.append("")
        L.append(f"**Authors:** {authors}  ")
        L.append(f"**Year:** {rec['year'] or '—'}  ")
        if rec["publication"]:
            L.append(f"**Published in:** {rec['publication']}  ")
        if rec["doi"]:
            L.append(f"**DOI:** {rec['doi']}  ")
        if rec["tags"]:
            L.append(f"**Tags:** {', '.join(rec['tags'])}  ")
        L.append("")
        if rec["abstract"]:
            L.append("### Abstract")
            L.append("")
            L.append(rec["abstract"])
            L.append("")
        highlights = [a for a in rec["annotations"] if a["highlighted_text"] or a["comment"]]
        if highlights:
            L.append("### Highlights & Annotations")
            L.append("")
            for a in highlights:
                page = f" (p. {a['page']})" if a["page"] else ""
                if a["highlighted_text"]:
                    L.append(f"> {a['highlighted_text']}{page}")
                if a["comment"]:
                    L.append(f">")
                    L.append(f"> 💬 *{a['comment']}*")
                L.append("")
        if rec["notes"]:
            L.append("### Notes")
            L.append("")
            for n in rec["notes"]:
                if n:
                    L.append(n)
                    L.append("")
        L.append("---")
        L.append("")
    return "\n".join(L)


# ----------------------------------------------------------------------------- main

def main():
    ap = argparse.ArgumentParser(description="Export a Zotero collection to JSON + Markdown.")
    ap.add_argument("--collection", help="Collection name to export")
    ap.add_argument("--db", default=str(default_db_path()), help="Path to zotero.sqlite")
    ap.add_argument("--out", default=".", help="Output directory")
    ap.add_argument("--list", action="store_true", help="List collection names and exit")
    args = ap.parse_args()

    conn = open_db(args.db)

    if args.list:
        for c in list_collections(conn):
            print(c)
        return

    if not args.collection:
        ap.error("--collection is required (or use --list)")

    cid = resolve_collection_id(conn, args.collection)
    item_rows = items_in_collection(conn, cid)
    records = [build_record(conn, r) for r in item_rows]

    out_dir = Path(args.out).expanduser()
    out_dir.mkdir(parents=True, exist_ok=True)
    safe = re.sub(r"[^\w\-]+", "_", args.collection).strip("_")

    json_path = out_dir / f"{safe}.json"
    md_path = out_dir / f"{safe}.md"

    payload = {"collection": args.collection, "item_count": len(records), "items": records}
    json_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    md_path.write_text(to_markdown(args.collection, records), encoding="utf-8")

    n_annot = sum(len(r["annotations"]) for r in records)
    print(f"✓ {len(records)} items, {n_annot} annotations")
    print(f"  JSON → {json_path}")
    print(f"  MD   → {md_path}")


if __name__ == "__main__":
    main()
