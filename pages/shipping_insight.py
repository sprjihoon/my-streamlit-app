# pages/shipping_insight.py – 전체 데이터 조회 전용
# -------------------------------------------------
from __future__ import annotations
import pandas as pd
import streamlit as st
from common import get_connection

st.set_page_config(page_title="🚚 통계 인사이트", layout="wide")
st.title("📊 전체 데이터 인사이트")

# 1) 테이블 선택
@st.cache_data(ttl=15)
def list_tables():
    with get_connection() as con:
        rows = con.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'").fetchall()
    return sorted(r[0] for r in rows)

table_sel = st.selectbox("📑 테이블 선택", list_tables(),
                         index=0 if "shipping_stats" not in list_tables() else list_tables().index("shipping_stats"))

@st.cache_data(ttl=15)
def load_table(tbl):
    with get_connection() as con:
        return pd.read_sql(f"SELECT * FROM {tbl}", con)

df = load_table(table_sel)

# ── 필수 컬럼 수동 지정 (간단화)
cols = df.columns.tolist()
col_vendor = st.selectbox("공급처 컬럼", cols, index=cols.index("공급처") if "공급처" in cols else 0)
col_item   = st.selectbox("상품(아이템) 컬럼", cols, index=cols.index("상품명") if "상품명" in cols else 0)
col_qty    = st.selectbox("수량 컬럼", cols, index=cols.index("수량") if "수량" in cols else 0)

# 공급처 멀티 필터
vendors = sorted(df[col_vendor].dropna().unique())
sel_vendors = st.multiselect("공급처 필터", vendors, default=vendors)
df = df[df[col_vendor].isin(sel_vendors)]

# 공급처별 수량 요약
st.subheader("📦 공급처별 수량 합계")
st.dataframe(df.groupby(col_vendor)[col_qty].sum().reset_index().rename(columns={col_qty:"수량"}),
             use_container_width=True)

# 상품 Top 20 (수량)
st.subheader("🏆 상품 Top 20 (수량)")
top20 = (df.groupby(col_item)[col_qty].sum().reset_index()
           .sort_values(col_qty, ascending=False).head(20))
st.dataframe(top20, use_container_width=True)
st.bar_chart(top20.set_index(col_item))

# 키워드 검색
st.subheader("🔍 상품 키워드 검색")
keyword = st.text_input("키워드")
if keyword:
    df_kw = df[df[col_item].str.contains(keyword, case=False, na=False)]
    st.metric("건수", f"{len(df_kw):,}")
    st.metric("수량", f"{df_kw[col_qty].sum():,}")
    st.dataframe(df_kw.head(100), use_container_width=True)
    st.download_button("CSV 다운로드",
                       df_kw.to_csv(index=False).encode("utf-8-sig"),
                       "filter.csv", "text/csv")
