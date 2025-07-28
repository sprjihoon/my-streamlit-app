import sqlite3, pandas as pd
db = r"C:\Users\one\Desktop\new_cal\billing.db"

VENDOR = "업피치"
d_from, d_to = "2025-03-01", "2025-03-31"

with sqlite3.connect(db) as con:
    wl = pd.read_sql(
        "SELECT DISTINCT 업체명 FROM work_log "
        "WHERE 날짜 BETWEEN ? AND ?", con, params=(d_from, d_to))
    print("① work_log 업체명 →", wl["업체명"].tolist())

    alias = pd.read_sql(
        "SELECT alias FROM aliases "
        "WHERE vendor=? AND file_type='work_log'", con, params=(VENDOR,))
    print("② aliases(work_log) →", alias["alias"].tolist())

    cache = pd.read_sql(
        "SELECT alias FROM alias_vendor_cache "
        "WHERE vendor=?", con, params=(VENDOR,))
    print("③ alias_vendor_cache →", cache["alias"].tolist())

    names = [VENDOR] + alias["alias"].tolist()
    q = ("SELECT * FROM work_log WHERE 업체명 IN ({}) "
         "AND 날짜 BETWEEN ? AND ?").format(",".join("?"*len(names)))
    df = pd.read_sql(q, con, params=(*names, d_from, d_to))
    print(f"④ work_log 필터 후 행 수 → {len(df)}")
    if not df.empty:
        print(df.head())
