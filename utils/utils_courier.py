import sqlite3, logging, json
import pandas as pd
import streamlit as st
from common import get_connection

def add_courier_fee_by_zone(vendor: str, d_from: str, d_to: str) -> None:
    """
    공급처 + 날짜 기준으로 kpost_in에서 부피 → 사이즈 구간 매핑 후,
    shipping_zone 요금표 적용하여 구간별 택배요금 항목을 session_state["items"]에 추가.
    """
    with get_connection() as con:
        # ① 공급처의 rate_type 확인
        cur = con.cursor()
        cur.execute("SELECT rate_type FROM vendors WHERE vendor = ?", (vendor,))
        row = cur.fetchone()
        rate_type = row[0] if row else "STD"

        # ② 별칭 목록 불러오기 (file_type = 'kpost_in')
        alias_df = pd.read_sql(
            "SELECT alias FROM alias_vendor_v WHERE vendor = ?",
            con, params=(vendor,)
        )
        name_list = [vendor] + alias_df["alias"].astype(str).str.strip().tolist()

        # ③ kpost_in 에서 부피 데이터 추출
        df_post = pd.read_sql(
            f"""
            SELECT 부피, 송장번호, 운송장번호, TrackingNo, tracking_no
            FROM kpost_in
            WHERE TRIM(발송인명) IN ({','.join('?' * len(name_list))})
              AND 접수일자 BETWEEN ? AND ?
            """, con, params=(*name_list, d_from, d_to)
        )
        # 발송인명 공백 제거 후 필터 누락 방지 완료

        if df_post.empty or "부피" not in df_post.columns:
            return

        # 부피값이 없거나 숫자가 아닌 경우 0으로 간주(극소 구간)
        df_post["부피"] = pd.to_numeric(df_post["부피"], errors="coerce").fillna(0)

        # 중복 송장 제거 → shipping_stats와 동일 기준
        for key_col in ("등기번호", "송장번호", "운송장번호", "TrackingNo", "tracking_no"):
            if key_col in df_post.columns:
                df_post = df_post.drop_duplicates(subset=[key_col])
                break

        # ④ shipping_zone 테이블에서 해당 요금제 구간 불러오기
        df_zone = pd.read_sql("SELECT * FROM shipping_zone WHERE 요금제 = ?", con, params=(rate_type,))
        # 숫자 형변환 (문자열/공백 → NaN) 후 정렬
        df_zone["len_min_cm"] = pd.to_numeric(df_zone["len_min_cm"], errors="coerce").fillna(0)
        df_zone["len_max_cm"] = pd.to_numeric(df_zone["len_max_cm"], errors="coerce")
        df_zone = df_zone.sort_values("len_min_cm").reset_index(drop=True)

        # ⑤ 구간 매핑 및 수량 집계
        size_counts: dict[str, dict] = {}
        for i, row in df_zone.iterrows():
            min_len = row["len_min_cm"]
            max_len = row["len_max_cm"]
            label = row["구간"]
            fee = row["요금"]

            # 마지막 구간은 하한 이상 전부 포함, 그 외 구간은 상한 포함 (≤ max)
            if pd.isna(max_len) or i == len(df_zone) - 1:
                cond = df_post["부피"] >= min_len
            else:
                cond = (df_post["부피"] >= min_len) & (df_post["부피"] <= max_len)

            count = df_post[cond].shape[0]
            if count > 0:
                size_counts[label] = {"count": count, "fee": fee}

        # 👉 디버그 로그 (터미널에 구간별 수량 표시)
        logging.warning("📦 SIZE DEBUG %s → %s", vendor, json.dumps(size_counts, ensure_ascii=False))

        # ⑥ session_state["items"]에 추가
        for label, info in size_counts.items():
            qty = info["count"]
            unit = info["fee"]
            st.session_state["items"].append({
                "항목": f"택배요금 ({label})",
                "수량": qty,
                "단가": unit,
                "금액": qty * unit
            })
