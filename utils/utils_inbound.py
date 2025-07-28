import sqlite3
import pandas as pd
import streamlit as st
from common import get_connection

def add_inbound_inspection_fee(vendor: str, d_from: str, d_to: str) -> None:
    """
    공급처 + 날짜 기준으로 inbound_slip에서 작업일자 필터,
    수량 총합 × out_extra 테이블 '입고검수' 단가 → 인보이스 항목 추가
    """
    with get_connection() as con:
        # ① 공급처 별칭 가져오기
        alias_df = pd.read_sql(
            "SELECT alias FROM aliases WHERE vendor = ? AND file_type = 'inbound_slip'",
            con, params=(vendor,)
        )
        name_list = [vendor] + alias_df["alias"].tolist()

        # ② 입고전표 로드 및 필터
        df = pd.read_sql(
            f"""
            SELECT 작업일, 수량, 공급처 FROM inbound_slip
            WHERE 공급처 IN ({','.join('?' * len(name_list))})
            """, con, params=name_list
        )

        if df.empty:
            return

        # 날짜 필터
        df["작업일"] = pd.to_datetime(df["작업일"], errors="coerce").dt.date
        d_from_dt = pd.to_datetime(d_from).date()
        d_to_dt = pd.to_datetime(d_to).date()
        df = df[(df["작업일"] >= d_from_dt) & (df["작업일"] <= d_to_dt)]

        if df.empty or "수량" not in df.columns:
            return

        total_qty = int(df["수량"].sum())

        # ③ 단가 가져오기 (out_extra 테이블)
        row = con.execute("SELECT 단가 FROM out_extra WHERE 항목 = '입고검수'").fetchone()
        unit = int(row[0]) if row else None

    if not unit:
        st.error("❗ '입고검수' 단가를 out_extra 테이블에서 찾을 수 없습니다.")
        return

    # ④ 인보이스 항목 추가
    st.session_state["items"].append({
        "항목": "입고검수",
        "수량": total_qty,
        "단가": unit,
        "금액": total_qty * unit
    })