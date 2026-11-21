"""A small recalls database for unit tests."""
import sqlite3

SCHEMA = """
CREATE TABLE recalls (
  recall_id INTEGER PRIMARY KEY,
  recall_number TEXT NOT NULL,
  title TEXT NOT NULL,
  recall_date TEXT NOT NULL,
  last_updated TEXT,
  description TEXT,
  hazard TEXT,
  remedy TEXT,
  remedy_type TEXT,
  product_name TEXT,
  product_type TEXT,
  units_text TEXT,
  units INTEGER,
  sold_at TEXT,
  manufactured_in TEXT,
  in_conjunction_with TEXT,
  url TEXT
);
CREATE TABLE notes (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  recall_number TEXT NOT NULL,
  author TEXT NOT NULL,
  body TEXT NOT NULL,
  created_at TEXT NOT NULL
);
CREATE TABLE load_log (
  run_at TEXT NOT NULL,
  status TEXT NOT NULL,
  rows_upserted INTEGER NOT NULL
);
"""

ROWS = [
    # number, title, date, product, hazard, units_text, units, sold_at
    ("25201", "Acme Recalls Space Heaters Due to Fire Hazard", "2025-03-01", "Space Heater", "Fire", "About 1,200", 1200, "Walmart stores nationwide"),
    ("25202", "Bolt Recalls Bike Helmets Due to Head Injury Hazard", "2025-06-01", "Bike Helmet", "Head injury", "About 900", 900, "Amazon.com"),
    ("26101", "Cedar Recalls Baby Loungers Due to Suffocation Hazard", "2026-01-10", "Baby Lounger", "Suffocation", "About 4,000", 4000, "Amazon.com"),
    ("26102", "Delta Recalls Power Banks Due to Fire Hazard", "2026-01-22", "Power Bank", "Fire", "About 15,000", 15000, "Target stores nationwide"),
    ("26103", "Echo Recalls Dressers Due to Tip-Over Hazard", "2026-02-03", "Dresser", "Tip-over", "About 700", 700, "Wayfair.com"),
    ("26104", "Fern Recalls Candles Due to Fire Hazard", "2026-02-17", "Candle", "Fire", "About 2,500", 2500, "Costco stores"),
    ("26105", "Gale Recalls Pajamas Due to Burn Hazard", "2026-02-28", "Pajamas", "Burn", "About 3,300", 3300, "Amazon.com"),
    ("26106", "Hale Recalls Stools Due to Fall Hazard", "2026-03-05", "Stool", "Fall", "About 8,000", 8000, "Walmart.com"),
    ("26107", "Iris Recalls Magnets Due to Ingestion Hazard", "2026-03-12", "Magnet Set", "Ingestion", "About 6,100", 6100, "Temu.com"),
    ("26108", "Juno Recalls E-Bikes Due to Fire Hazard", "2026-03-20", "E-Bike", "Fire", "About 450", 450, "Juno.com"),
]


def build(path: str) -> None:
    con = sqlite3.connect(path)
    con.executescript(SCHEMA)
    for i, (number, title, date, product, hazard, units_text, units, sold_at) in enumerate(ROWS, start=1):
        con.execute(
            "INSERT INTO recalls VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (i, number, title, date, date, f"This recall involves {product}.", hazard, "Stop using it and contact the firm.",
             "Refund", product, "Household", units_text, units, sold_at, "China", "", f"https://example.test/recalls/{number}"),
        )
    con.execute("INSERT INTO load_log VALUES ('2026-03-24T02:00:07Z', 'ok', 0)")
    con.execute("INSERT INTO load_log VALUES ('2026-03-25T02:00:07Z', 'ok', 1)")
    con.commit()
    con.close()
