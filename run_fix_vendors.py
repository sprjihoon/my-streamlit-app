import sqlite3, pathlib, textwrap

db = pathlib.Path(r"C:\Users\one\Desktop\new_cal\billing.db")
with sqlite3.connect(db) as con:
    cols = [c[1] for c in con.execute("PRAGMA table_info(vendors);")]
    # 없으면 컬럼 추가
    for c in ("name", "rate_type", "sku_group"):
        if c not in cols:
            con.execute(f"ALTER TABLE vendors ADD COLUMN {c} TEXT;")
    # vendor 비어 있는 레거시 행 → name 값 복사
    con.execute("""
        UPDATE vendors
           SET vendor = name
         WHERE (vendor IS NULL OR vendor = '')
           AND name IS NOT NULL AND name <> '';
    """)
    # 고유 인덱스
    con.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_vendor ON vendors(vendor);")

print("✅ vendors 테이블 스키마·데이터 보강 완료")
