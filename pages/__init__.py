import sqlite3
SQL = """
CREATE VIEW IF NOT EXISTS alias_vendor_v AS
SELECT vendor, alias, file_type
FROM   alias_vendor;
"""
with sqlite3.connect("billing.db") as con:
    con.executescript(SQL)
print("✅ alias_vendor_v view created (or already exists).")
