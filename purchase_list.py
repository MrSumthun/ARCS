# purchase_list.py - generate a purchase list from saved quotes
## flags --aggregate: legacy behavior, aggregate all parts across all quotes
##       --json: output JSON instead of text table

from __future__ import annotations

import argparse
import json
import os
import sys
from collections import defaultdict
from typing import Dict, Any, List

# Try to reuse arcs' load path when possible without importing the whole UI
# Fallback: look for data/quotes.json in repo or user data dir

REPO_ROOT = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
BUNDLED_QUOTES = os.path.join(REPO_ROOT, "data", "quotes.json")
USER_QUOTE_DIR = os.path.join(os.path.expanduser("~"), ".arcsoftware")
USER_QUOTES = os.path.join(USER_QUOTE_DIR, "quotes.json")


def load_quotes_from(path: str):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []


def find_quotes_file(preferred: str | None = None) -> str | None:
    # If explicit path provided and exists -> use it
    if preferred:
        if os.path.exists(preferred):
            return preferred
        print(f"Warning: requested file {preferred} not found.")
        return None
    # user file takes precedence
    if os.path.exists(USER_QUOTES):
        return USER_QUOTES
    # fall back to bundled quotes
    if os.path.exists(BUNDLED_QUOTES):
        return BUNDLED_QUOTES
    return None


def aggregate_parts(quotes: List[Dict[str, Any]]):
    # key by part_number and source; sum quantities and keep a representative unit_cost/list_price
    agg: Dict[tuple, Dict[str, Any]] = {}
    for q in quotes:
        for it in q.get("items", []) or []:
            pn = (it.get("part_number") or "<unknown>").strip()
            src = (it.get("source") or "<unknown>").strip()
            qty = int(it.get("quantity") or 0)
            unit = float(it.get("unit_cost") or 0.0)
            listp = float(it.get("list_price") or 0.0)
            key = (pn, src)
            entry = agg.get(key)
            if not entry:
                agg[key] = {
                    "part_number": pn,
                    "source": src,
                    "quantity": qty,
                    "unit_cost": unit,
                    "list_price": listp,
                }
            else:
                entry["quantity"] += qty
                # if unit_cost differs, keep the lowest (prefer cheaper supplier)
                if unit < entry.get("unit_cost", unit):
                    entry["unit_cost"] = unit
                if listp < entry.get("list_price", listp):
                    entry["list_price"] = listp
    # Return a sorted list by part number
    return sorted(agg.values(), key=lambda x: (x["part_number"], x["source"]))


def print_table(rows):
    # simple column widths
    cols = ["Part", "Qty", "Source", "Unit Cost", "List Price"]
    widths = [max(len(c), 12) for c in cols]
    # compute widths from rows
    for r in rows:
        widths[0] = max(widths[0], len(str(r["part_number"])))
        widths[1] = max(widths[1], len(str(r["quantity"])))
        widths[2] = max(widths[2], len(str(r["source"])))
    fmt = "  ".join(f"{{:<{w}}}" for w in widths)

    print(fmt.format(*cols))
    print("-" * (sum(widths) + 2 * (len(widths) - 1)))
    for r in rows:
        print(fmt.format(r["part_number"], r["quantity"], r["source"], f"{r['unit_cost']:.2f}", f"{r['list_price']:.2f}"))


def print_per_quote(quotes: List[Dict[str, Any]]):
    """Print parts grouped per quote (no global aggregation)."""
    if not quotes:
        print("No quotes to show.")
        return
    for i, q in enumerate(quotes, start=1):
        name = q.get("name") or f"Quote {i} (id: {q.get('id','?')})"
        items = q.get("items") or []
        if not items:
            print(f"\n{name}: (no items)")
            continue
        # Aggregate within the quote to merge duplicate line items in same quote
        agg: Dict[tuple, Dict[str, Any]] = {}
        for it in items:
            pn = (it.get("part_number") or "<unknown>").strip()
            src = (it.get("source") or "<unknown>").strip()
            qty = int(it.get("quantity") or 0)
            unit = float(it.get("unit_cost") or 0.0)
            listp = float(it.get("list_price") or 0.0)
            key = (pn, src)
            entry = agg.get(key)
            if not entry:
                agg[key] = {
                    "part_number": pn,
                    "source": src,
                    "quantity": qty,
                    "unit_cost": unit,
                    "list_price": listp,
                }
            else:
                entry["quantity"] += qty
                if unit < entry.get("unit_cost", unit):
                    entry["unit_cost"] = unit
                if listp < entry.get("list_price", listp):
                    entry["list_price"] = listp
        rows = sorted(agg.values(), key=lambda x: (x["part_number"], x["source"]))
        po = q.get("po_number")
        print("\n" + "=" * 60)
        if po:
            print(f"{name}   [PO: {po}]")
        else:
            print(f"{name}")
        print("-" * 60)
        print_table(rows)
    print()


def main(argv=None):
    p = argparse.ArgumentParser(description="Aggregate parts across saved quotes for purchasing")
    p.add_argument("--file", "-f", help="Path to quotes.json to use (overrides defaults)")
    p.add_argument("--json", action="store_true", help="Output JSON instead of a table")
    p.add_argument("--aggregate", action="store_true", help="Aggregate parts across all quotes (legacy behavior)")
    args = p.parse_args(argv)

    qf = find_quotes_file(args.file)
    if not qf:
        print("No quotes file found (tried user data and bundled data). Create a quote first.")
        return 2

    quotes = load_quotes_from(qf)

    # Default: per-quote summaries. Use --aggregate to get the old aggregate behavior.
    if not args.aggregate:
        if args.json:
            per = []
            for i, q in enumerate(quotes, start=1):
                # aggregate within each quote for compact JSON
                items = q.get("items") or []
                agg = {}
                for it in items:
                    pn = (it.get("part_number") or "<unknown>").strip()
                    src = (it.get("source") or "<unknown>").strip()
                    qty = int(it.get("quantity") or 0)
                    unit = float(it.get("unit_cost") or 0.0)
                    listp = float(it.get("list_price") or 0.0)
                    key = (pn, src)
                    entry = agg.get(key)
                    if not entry:
                        agg[key] = {
                            "part_number": pn,
                            "source": src,
                            "quantity": qty,
                            "unit_cost": unit,
                            "list_price": listp,
                        }
                    else:
                        entry["quantity"] += qty
                        if unit < entry.get("unit_cost", unit):
                            entry["unit_cost"] = unit
                        if listp < entry.get("list_price", listp):
                            entry["list_price"] = listp
                per.append({
                    "quote": q.get("name") or f"Quote {i}",
                    "po": q.get("po_number"),
                    "parts": sorted(agg.values(), key=lambda x: (x["part_number"], x["source"]))
                })
            print(json.dumps(per, indent=2))
            return 0
        else:
            print_per_quote(quotes)
            return 0

    # Aggregate across all quotes (legacy behavior)
    parts = aggregate_parts(quotes)

    if args.json:
        print(json.dumps(parts, indent=2))
        return 0

    if not parts:
        print("No parts found in quotes.")
        print("Create quotes with items to generate a purchase list.")
        return 0

    print_table(parts)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
