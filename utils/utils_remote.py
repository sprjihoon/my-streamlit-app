import sqlite3
import pandas as pd
import streamlit as st
from common import get_connection

def add_remote_area_fee(vendor: str, d_from: str, d_to: str) -> None:
    """
    공급처 + 날짜 기준으로 kpost_in에서 '도서행' == 'y'인 건수 계산,
    단가(out_extra) 적용 → '도서산간' 항목 인보이스에 추가
    """
    with get_connection() as con:
        # ① 공급처 + 별칭 목록
        alias_df = pd.read_sql(
            "SELECT alias FROM alias_vendor_v WHERE vendor = ?",
            con, params=(vendor,)
        )
        name_list = [vendor] + alias_df["alias"].astype(str).str.strip().tolist()

        # ② kpost_in 필터 + 도서행 여부 확인
        df = pd.read_sql(
            f"""
            SELECT 도서행 FROM kpost_in
            WHERE TRIM(발송인명) IN ({','.join('?' * len(name_list))})
              AND 접수일자 BETWEEN ? AND ?
            """, con, params=(*name_list, d_from, d_to)
        )

    if df.empty or "도서행" not in df.columns:
        st.warning(f"📭 '{vendor}' 도서산간 데이터 없음 or '도서행' 칼럼 없음")
        return

    # 2025-07-28: 일부 파일은 도서행 표기가 누락되어 전체 건수를 사용
    df["도서행"] = df["도서행"].astype(str).str.lower().str.strip()
    qty = df[df["도서행"] == "y"].shape[0]

    st.info(f"✅ {vendor} 도서산간 적용 수량: {qty}")

    if qty == 0:
        return

    try:
        with sqlite3.connect("billing.db") as con:
            row = con.execute("SELECT 단가 FROM out_extra WHERE 항목 = '도서산간'").fetchone()
            unit = int(row[0]) if row else None
    except Exception:
        unit = None

    if not unit:
        st.error("❗ out_extra 테이블에서 '도서산간' 단가를 찾을 수 없습니다.")
        return

    st.session_state["items"].append({
        "항목": "도서산간",
        "수량": qty,
        "단가": unit,
        "금액": qty * unit
    })