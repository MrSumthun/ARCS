from __future__ import annotations

import argparse
import json
import os
from typing import Dict, Any, List

REPO_ROOT = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
BUNDLED_QUOTES = os.path.join(REPO_ROOT, "data", "quotes.json")
USER_QUOTE_DIR = os.path.join(os.path.expanduser("~"), ".arcsoftware")
USER_QUOTES = os.path.join(USER_QUOTE_DIR, "quotes.json")
# --json: output JSON instead of text table
# Wrote this code with a couple of beers, only God knows how it works now.


def load_quotes_from(path: str):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []


def find_quotes_file(preferred: str | None = None) -> str | None:
    if preferred:
        if os.path.exists(preferred):
            return preferred
        print(f"Warning: requested file {preferred} not found.")
        return None

    if os.path.exists(USER_QUOTES):
        return USER_QUOTES

    if os.path.exists(BUNDLED_QUOTES):
        return BUNDLED_QUOTES
    return None


def print_table(rows):
    # simple column widths (includes Tax Exempt flag)
    cols = ["Part", "Qty", "Source", "Unit Cost", "List Price", "Tax Exempt"]
    widths = [max(len(c), 12) for c in cols]
    # compute widths from rows
    for r in rows:
        widths[0] = max(widths[0], len(str(r["part_number"])))
        widths[1] = max(widths[1], len(str(r["quantity"])))
        widths[2] = max(widths[2], len(str(r["source"])))
        widths[5] = max(widths[5], len("Yes") if r.get("tax_exempt") else widths[5])
    fmt = "  ".join(f"{{:<{w}}}" for w in widths)

    print(fmt.format(*cols))
    print("-" * (sum(widths) + 2 * (len(widths) - 1)))
    for r in rows:
        tax_col = "Yes" if r.get("tax_exempt") else ""
        print(
            fmt.format(
                r["part_number"],
                r["quantity"],
                r["source"],
                f"{r['unit_cost']:.2f}",
                f"{r['list_price']:.2f}",
                tax_col,
            )
        )


def print_per_quote(quotes: List[Dict[str, Any]]):
    if not quotes:
        print("No quotes to show.")
        return
    for i, q in enumerate(quotes, start=1):
        name = q.get("name") or f"Quote {i} (id: {q.get('id', '?')})"
        items = q.get("items") or []
        if not items:
            print(f"\n{name}: (no items)")
            continue

        # Compute supplier tax-exempt status from item flags
        supplier_exempt: Dict[str, bool] = {}
        for it in items:
            src = (it.get("source") or "<unknown>").strip()
            supplier_exempt[src] = supplier_exempt.get(src, False) or bool(it.get("tax_exempt", False))

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
                    "tax_exempt": bool(it.get("tax_exempt", False)),
                }
            else:
                entry["quantity"] += qty
                if unit < entry.get("unit_cost", unit):
                    entry["unit_cost"] = unit
                if listp < entry.get("list_price", listp):
                    entry["list_price"] = listp
                entry["tax_exempt"] = entry.get("tax_exempt", False) or bool(it.get("tax_exempt", False))
        rows = sorted(agg.values(), key=lambda x: (x["part_number"], x["source"]))
        po = q.get("po_number")
        print("\n" + "=" * 60)
        if po:
            print(f"{name}   [PO: {po}]")
        else:
            print(f"{name}")
        print("-" * 60)
        # Print suppliers and their tax status
        if supplier_exempt:
            print("Suppliers:")
            for s in sorted(supplier_exempt.keys()):
                status = " (Tax Exempt)" if supplier_exempt.get(s) else ""
                print(f"  {s}{status}")
            # Print a concise list of tax-exempt suppliers if any
            exempt_suppliers = sorted([s for s, v in supplier_exempt.items() if v])
            if exempt_suppliers:
                print("Tax-exempt suppliers: " + ", ".join(exempt_suppliers))
            print("-" * 60)
        print_table(rows)
    print()


def main(argv=None):
    p = argparse.ArgumentParser(description="Show parts per quote for purchasing")
    p.add_argument(
        "--file", "-f", help="Path to quotes.json to use (overrides defaults)"
    )
    p.add_argument("--json", action="store_true", help="Output JSON instead of a table")
    args = p.parse_args(argv)

    qf = find_quotes_file(args.file)
    if not qf:
        print(
            "No quotes file found (tried user data and bundled data). Create a quote first."
        )
        return 2

    quotes = load_quotes_from(qf)

    if args.json:
        per = []
        for i, q in enumerate(quotes, start=1):
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
                        "tax_exempt": bool(it.get("tax_exempt", False)),
                    }
                else:
                    entry["quantity"] += qty
                    if unit < entry.get("unit_cost", unit):
                        entry["unit_cost"] = unit
                    if listp < entry.get("list_price", listp):
                        entry["list_price"] = listp
                    entry["tax_exempt"] = entry.get("tax_exempt", False) or bool(it.get("tax_exempt", False))
            per.append(
                {
                    "quote": q.get("name") or f"Quote {i}",
                    "po": q.get("po_number"),
                    "parts": sorted(
                        agg.values(), key=lambda x: (x["part_number"], x["source"])
                    ),
                }
            )
        print(json.dumps(per, indent=2))
        return 0

    print_per_quote(quotes)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
