# utils/db_helpers.py
import re, sqlite3, pandas as pd
from datetime import date
from typing import List

BILLING_DB   = "billing.db"
_rx_delim    = re.compile(r"[./]")        # 날짜 구분자 통일용

# ─────────────────────────────────────
# 업체 목록 (alias_map → vendors 순으로 탐색)
# ─────────────────────────────────────
def vendor_list() -> List[str]:
    with sqlite3.connect(BILLING_DB) as con:
        tables = {r[0] for r in con.execute(
            "SELECT name FROM sqlite_master WHERE type='table'")}
        for tbl in ("alias_map", "vendors"):
            if tbl in tables:
                rows = con.execute(f"SELECT DISTINCT vendor FROM {tbl}").fetchall()
                if rows:
                    return sorted(r[0] for r in rows)
    return []

# ─────────────────────────────────────
# 배송통계 필터  (LIKE '%vendor%'  방식)
# ─────────────────────────────────────
def shipping_stats(vendor: str,
                   d_from:  date,
                   d_to:    date,
                   date_col: str = "배송일") -> pd.DataFrame:
    """
    * alias_map 이 없어도 동작.
    * 공급처 LIKE '%vendor%' 로 부분 일치 검색해 내 물량을 집계한다.
    * 날짜 구분자 /·. 를 - 로 통일, 시간 정보는 앞 10글자(YYYY-MM-DD)만 사용.
    """
    with sqlite3.connect(BILLING_DB) as con:
        # 날짜 컬럼 자동 대체: '배송일' 없으면 '송장등록일' 사용
        cols = [r[1] for r in con.execute("PRAGMA table_info(shipping_stats)")]
        if date_col not in cols and "송장등록일" in cols:
            date_col = "송장등록일"

        df = pd.read_sql(
            f"""
            SELECT 공급처, [{date_col}] AS dt
            FROM   shipping_stats
            WHERE  공급처 LIKE '%' || ? || '%'
              AND  DATE([{date_col}]) BETWEEN ? AND ?
            """,
            con,
            params=(vendor, d_from.isoformat(), d_to.isoformat()),
        )

    # 날짜 전처리 → datetime64
    df["dt"] = (
        df["dt"].astype(str)
        .str.replace(_rx_delim, "-", regex=True)  # /·. → -
        .str.slice(0, 10)                         # YYYY-MM-DD HH:MM → YYYY-MM-DD
        .pipe(pd.to_datetime, errors="coerce")
    )

    return df
