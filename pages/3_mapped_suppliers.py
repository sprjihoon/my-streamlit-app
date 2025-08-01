import pandas as pd
import streamlit as st
from common import get_connection
from typing import List

"""
pages/3_mapped_suppliers.py – 매핑된 공급처(서플라이어) 리스트 관리
────────────────────────────────────────────────────────
* vendors & aliases 테이블을 읽어 매핑 현황을 확인·수정·삭제
* vendors 테이블에 vendor 컬럼이 없을 경우 버전 호환 방식으로 자동 생성
* FLAG_COLS 는 2_mapping_manager.py 와 동일 플래그 사용
* 별칭(alias) 편집 UI 를 multiselect 로 개선
"""

# ─────────────────────────────────────
# 0. 스키마 보강: vendor 컬럼 보장 (SQLite 구버전 호환)
# ─────────────────────────────────────
with get_connection() as con:
    cols = [c[1] for c in con.execute("PRAGMA table_info(vendors);")]
    if "vendor" not in cols:
        con.execute("ALTER TABLE vendors ADD COLUMN vendor TEXT;")
        # name → vendor 복사 (name 이 있을 때만)
        if "name" in cols:
            con.execute("UPDATE vendors SET vendor = name WHERE vendor IS NULL OR vendor = '';")
        # 고유 인덱스
        con.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_vendor ON vendors(vendor);")

# ─────────────────────────────────────
# 1. 상수 정의
# ─────────────────────────────────────
SKU_OPTS  = ["≤100", "≤300", "≤500", "≤1,000", "≤2,000", ">2,000"]
FLAG_COLS = [
    "barcode_f", "custbox_f", "void_f", "pp_bag_f",
    "video_out_f", "video_ret_f",
]
FILE_TYPES = [
    "inbound_slip", "shipping_stats", "kpost_in", "kpost_ret", "work_log",
]
SRC_TABLES = [
    ("inbound_slip","공급처",    "inbound_slip"),
    ("shipping_stats","공급처",  "shipping_stats"),
    ("kpost_in","발송인명",      "kpost_in"),
    ("kpost_ret","수취인명",     "kpost_ret"),
    ("work_log","업체명",        "work_log"),
]


# ─────────────────────────────────────
# 2. Streamlit 초기화
# ─────────────────────────────────────
try:
    st.set_page_config(page_title="매핑 리스트", layout="wide")
except Exception:
    pass
st.title("📋 공급처 매핑 리스트")

# ─────────────────────────────────────
# 3. 데이터 로드 (캐시 15초)
# ─────────────────────────────────────
@st.cache_data(ttl=15)
def load_all():
    with get_connection() as con:
        df_v = pd.read_sql("SELECT * FROM vendors ORDER BY vendor", con)
        df_a = pd.read_sql("SELECT * FROM aliases", con)
    for col in FLAG_COLS:
        if col not in df_v.columns:
            df_v[col] = "NO"
    return df_v, df_a

@st.cache_data(ttl=15)
def get_all_aliases_from_source():
    """원본 테이블에서 모든 alias 목록을 가져옵니다."""
    all_aliases = {}
    with get_connection() as con:
        for tbl, col, ft in SRC_TABLES:
            try:
                # 테이블 및 컬럼 존재 여부 확인
                tables = pd.read_sql("SELECT name FROM sqlite_master WHERE type='table'", con)
                if tbl not in tables['name'].values:
                    all_aliases[ft] = []
                    continue
                
                cols_in_tbl = [c[1] for c in con.execute(f"PRAGMA table_info({tbl});")]
                if col not in cols_in_tbl:
                    all_aliases[ft] = []
                    continue

                df = pd.read_sql(f"SELECT DISTINCT [{col}] as alias FROM {tbl}", con)
                aliases = [str(x).strip() for x in df.alias.dropna() if str(x).strip()]
                all_aliases[ft] = sorted(list(set(aliases)))
            except Exception:
                 all_aliases[ft] = []
    return all_aliases

df_vendors, df_alias = load_all()
if df_vendors.empty:
    st.info("등록된 공급처가 없습니다. 매핑 매니저에서 먼저 추가하세요.")
    st.stop()
    
all_source_aliases = get_all_aliases_from_source()

# ─────────────────────────────────────
# 4. 검색 & 메인 리스트
# ─────────────────────────────────────
kw = st.text_input("검색어(공급처/별칭)").strip().lower()
if kw:
    matched = df_alias[df_alias.alias.str.lower().str.contains(kw)].vendor.unique()
    df_disp = df_vendors[
        df_vendors.vendor.str.lower().str.contains(kw) | df_vendors.vendor.isin(matched)
    ]
else:
    df_disp = df_vendors.copy()

main_cols = [
    "vendor", "rate_type", "sku_group",
    "barcode_f", "custbox_f", "void_f", "pp_bag_f",
    "video_out_f", "video_ret_f",
]

st.dataframe(df_disp[main_cols], use_container_width=True, height=400)

# ─────────────────────────────────────
# 5. 상세 편집 영역
# ─────────────────────────────────────
sel_vendor = st.selectbox("✏️ 수정/삭제할 공급처", [""] + df_vendors.vendor.tolist())
if not sel_vendor:
    st.stop()

row_v = df_vendors[df_vendors.vendor == sel_vendor].iloc[0]
df_alias_v = df_alias[df_alias.vendor == sel_vendor]

def get_options_and_defaults(file_type: str) -> (List[str], List[str]):
    """multiselect 에 필요한 옵션과 기본값을 반환합니다."""
    default_aliases = df_alias_v[df_alias_v.file_type == file_type].alias.tolist()
    source_aliases = all_source_aliases.get(file_type, [])
    options = sorted(list(set(default_aliases + source_aliases)))
    return options, default_aliases

# 파일 타입별로 multiselect 생성
inb_opts, inb_defs = get_options_and_defaults("inbound_slip")
ship_opts, ship_defs = get_options_and_defaults("shipping_stats")
kpin_opts, kpin_defs = get_options_and_defaults("kpost_in")
ktrt_opts, ktrt_defs = get_options_and_defaults("kpost_ret")
wl_opts, wl_defs = get_options_and_defaults("work_log")

inb  = st.multiselect("입고전표 별칭", inb_opts, default=inb_defs)
ship = st.multiselect("배송통계 별칭", ship_opts, default=ship_defs)
kpin = st.multiselect("우체국접수 별칭", kpin_opts, default=kpin_defs)
ktrt = st.multiselect("우체국반품 별칭", ktrt_opts, default=ktrt_defs)
wl   = st.multiselect("작업일지 별칭", wl_opts, default=wl_defs)

l, r = st.columns(2)
rate_type   = l.selectbox("요금타입", ["A", "STD"], index=["A", "STD"].index(row_v.rate_type or "A"))
sku_group   = r.selectbox("SKU 구간", SKU_OPTS, index=SKU_OPTS.index(row_v.sku_group or SKU_OPTS[0]))
barcode_f   = l.selectbox("바코드 부착", ["YES", "NO"], index=["YES", "NO"].index(row_v.barcode_f or "NO"))
custbox_f   = l.selectbox("박스", ["YES", "NO"], index=["YES", "NO"].index(row_v.custbox_f or "NO"))
void_f      = r.selectbox("완충재", ["YES", "NO"], index=["YES", "NO"].index(row_v.void_f or "NO"))
pp_bag_f    = r.selectbox("PP 봉투", ["YES", "NO"], index=["YES", "NO"].index(row_v.pp_bag_f or "NO"))
video_out_f = l.selectbox("출고영상촬영", ["YES", "NO"], index=["YES", "NO"].index(row_v.video_out_f or "NO"))
video_ret_f = l.selectbox("반품영상촬영", ["YES", "NO"], index=["YES", "NO"].index(row_v.video_ret_f or "NO"))

save_col, del_col = st.columns(2)

# ─────────────────────────────────────
# 6. 저장
# ─────────────────────────────────────
if save_col.button("💾 변경 사항 저장"):
    try:
        with get_connection() as con:
            con.execute(
                """UPDATE vendors SET rate_type=?, sku_group=?, barcode_f=?, custbox_f=?, void_f=?, pp_bag_f=?, video_out_f=?, video_ret_f=? WHERE vendor=?""",
                (
                    rate_type, sku_group, barcode_f, custbox_f,
                    void_f, pp_bag_f, video_out_f, video_ret_f, sel_vendor,
                ),
            )
            con.execute("DELETE FROM aliases WHERE vendor=?", (sel_vendor,))
            def _ins(ft: str, lst: List[str]):
                for a in lst:
                    con.execute("INSERT INTO aliases VALUES (?,?,?)", (a, sel_vendor, ft))
            _ins("inbound_slip", inb)
            _ins("shipping_stats", ship)
            _ins("kpost_in", kpin)
            _ins("kpost_ret", ktrt)
            _ins("work_log", wl)
        st.cache_data.clear()
        st.success("저장 완료!")
        st.rerun()
    except Exception as e:
        st.error(f"❌ 업데이트 실패: {e}")

# ─────────────────────────────────────
# 7. 삭제
# ─────────────────────────────────────
if del_col.button("🗑 공급처 삭제", type="secondary"):
    try:
        if st.radio("정말 삭제할까요?", ["취소", "삭제"], horizontal=True, index=0) == "삭제":
            with get_connection() as con:
                con.execute("DELETE FROM vendors WHERE vendor=?", (sel_vendor,))
                con.execute("DELETE FROM aliases WHERE vendor=?", (sel_vendor,))
            st.cache_data.clear()
            st.success("삭제 완료")
            st.rerun()
    except Exception as e:
        st.error(f"❌ 삭제 실패: {e}")
