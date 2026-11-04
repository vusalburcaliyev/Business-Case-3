"""Load the official AdventureWorksDW install ZIP and rebuild the sales case."""
import argparse
from collections import Counter
import csv
from datetime import datetime
from decimal import Decimal
import io
import json
from pathlib import Path
import sqlite3
from zipfile import ZipFile

ROOT = Path(__file__).resolve().parents[1]


def records(z, name, width):
    with io.TextIOWrapper(z.open(name + ".csv"), encoding="utf-8-sig") as f:
        for n, line in enumerate(f, 1):
            row = line.rstrip("\r\n").split("|")
            if len(row) != width:
                raise ValueError(f"{name} row {n}: unexpected column count")
            yield row


def dollars4(raw):
    value = Decimal(raw) * 10000
    if not value.is_finite() or value != value.to_integral_value():
        raise ValueError(f"Expected a source money value with up to four decimals: {raw}")
    return int(value)


def prepare(db, archive):
    audit = Counter()
    db.executescript((ROOT / "sql/00_model.sql").read_text(encoding="utf-8"))
    with ZipFile(archive) as z, db:
        for table, name, width, transform in [
            ("category", "DimProductCategory", 5, lambda x: (int(x[0]), x[2].strip())),
            ("subcategory", "DimProductSubcategory", 6, lambda x: (int(x[0]), int(x[5]))),
            ("product", "DimProduct", 36, lambda x: (int(x[0]), int(x[2]) if x[2] else None, x[5].strip())),
            ("territory", "DimSalesTerritory", 6, lambda x: (int(x[0]), x[2].strip(), x[3].strip())),
            ("currency", "DimCurrency", 3, lambda x: (int(x[0]), x[1].strip().upper())),
        ]:
            rows = [transform(x) for x in records(z, name, width)]
            db.executemany(f"INSERT INTO {table} VALUES ({','.join('?' * len(rows[0]))})", rows)
            audit[f"source_{table}_rows"] = len(rows)

        for channel, name, shift in [("Internet", "FactInternetSales", 0), ("Reseller", "FactResellerSales", 1)]:
            distinct = {}
            for x in records(z, name, 26 + shift):
                audit[f"source_{channel.lower()}_lines"] += 1
                day = datetime.strptime(x[1], "%Y%m%d").date().isoformat()
                if day != x[23 + shift][:10]:
                    raise ValueError("Order date key and source order date differ")
                product_id, territory_id, currency_id = map(int, (x[0], x[7 + shift], x[6 + shift]))
                order_no = x[8 + shift].strip()
                if not order_no:
                    raise ValueError("Missing order ID")
                line_no, units = map(int, (x[9 + shift], x[11 + shift]))
                gross, revenue, cost = map(dollars4, (x[13 + shift], x[18 + shift], x[17 + shift]))
                # Source DiscountAmount is a float; test within one 0.0001 money unit.
                if abs(Decimal(gross - revenue) - Decimal(x[15 + shift]) * 10000) > Decimal("1.001"):
                    raise ValueError("Sales amount does not reconcile with recorded discount")
                key = (order_no, line_no)
                value = (day, product_id, territory_id, currency_id, units, gross, revenue, cost)
                if key in distinct:
                    if value != distinct[key]:
                        raise ValueError(f"Conflicting order line {channel}, {key}")
                    audit["duplicate_lines_removed"] += 1
                distinct[key] = value
            db.executemany("INSERT INTO sale VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                           ((channel, *k, *v) for k, v in distinct.items()))
    audit.setdefault("duplicate_lines_removed", 0)
    audit["scoped_lines"] = db.execute("SELECT COUNT(*) FROM scoped").fetchone()[0]
    audit["scoped_uncategorized_lines"] = db.execute("SELECT COUNT(*) FROM scoped WHERE category='Unclassified'").fetchone()[0]
    audit["scoped_negative_profit_lines"] = db.execute("SELECT COUNT(*) FROM scoped WHERE profit<0").fetchone()[0]
    if db.execute("PRAGMA foreign_key_check").fetchone() is not None:
        raise ValueError("Unmatched source key")
    return audit


def export(db, audit):
    payload = {}
    for path in sorted((ROOT / "sql").glob("0[1-9]_*.sql")):
        cursor = db.execute(path.read_text(encoding="utf-8"))
        header = [field[0] for field in cursor.description]
        rows = cursor.fetchall()
        payload[path.stem] = [dict(zip(header, row)) for row in rows]
        with (ROOT / f"results/{path.stem}.csv").open("w", encoding="utf-8", newline="") as f:
            writer = csv.writer(f, lineterminator="\n")
            writer.writerow(header)
            writer.writerows(rows)
    monthly = payload["02_monthly_trend"]
    expected = [f"{y}-{m:02d}" for y in (2012, 2013) for m in range(1, 13)]
    assert [m["month"] for m in monthly] == expected, "LAG needs a complete monthly series"
    for y in ("2012","2013"):
        totals = [r for r in payload["01_channel_scorecard"] if r["year"]==y]
        total = next(r for r in totals if r["channel"]=="All channels")
        groups = [r for r in totals if r["channel"]!="All channels"]
        for key, tolerance in [("sales_usd",.03),("profit_usd",.03),("orders",0),("units",0)]:
            assert abs(sum(r[key] for r in groups)-total[key]) <= tolerance
        for key in ("sales_usd","profit_usd"):
            assert abs(sum(m[key] for m in monthly if m["month"].startswith(y))-total[key]) <= .08
            assert abs(sum(r[key] for r in payload["03_category_rank"] if r["year"]==y)-total[key]) <= .03
            assert abs(sum(r[key] for r in payload["04_discount_review"] if r["year"]==y)-
                       next(r[key] for r in groups if r["channel"]=="Reseller")) <= .02
        trimmed = next(r for r in payload["05_order_sensitivity"] if r["year"]==y)
        assert trimmed["orders"] == total["orders"] and 0 < trimmed["above_cutoff"] < total["orders"]
    (ROOT / "results/audit.json").write_text(json.dumps(audit, indent=2, sort_keys=True)+"\n", encoding="utf-8")
    print("Verified: 24 consecutive months, matching channel/category/discount totals and order counts.")
    return payload


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("archive", type=Path)
    args = parser.parse_args()
    with sqlite3.connect(":memory:") as db:
        audit = prepare(db, args.archive)
        payload = export(db, audit)
    print(json.dumps(audit, sort_keys=True))
    template = ROOT / "dashboard/template.html"
    if template.exists():
        from previews import make
        content = json.dumps(payload, separators=(",", ":"), ensure_ascii=True).replace("<","\\u003c")
        (ROOT / "Sales_Dashboard.html").write_text(
            template.read_text(encoding="utf-8").replace("/* @RESULTS */",content), encoding="utf-8")
        make(ROOT, payload)


if __name__ == "__main__":
    main()
