# 📊 New-Cal 홈 (엔트리포인트)
import sys, pathlib

# ── 0) 패키지 경로 주입 ─────────────────────────────
ROOT      = pathlib.Path(__file__).resolve().parent      # …/new_cal
PARENTDIR = ROOT.parent                                  # Desktop
if str(PARENTDIR) not in sys.path:
    sys.path.insert(0, str(PARENTDIR))                   # new_cal import 가능

# ── 1) 일반 import ─────────────────────────────────
import streamlit as st
from datetime import date

# ── 2) 페이지 설정 ─────────────────────────────────
st.set_page_config(page_title="New-Cal 홈", page_icon="📊", layout="wide")
st.title("📊 New-Cal Dashboard / Landing Page")

st.write(
    """
    **환영합니다!**  
    왼쪽 사이드바에서 기능을 선택하세요.

    > Upload → Mapping → Unit Price → Invoice 순으로 업무를 진행합니다.
    """
)

# ── 3) 사이드바 네비게이션 ──────────────────────────
with st.sidebar:
    st.header("🔗 메뉴")
    st.page_link("pages/1_upload_manager.py", label="📤 업로드 매니저")
    # 아직 없는 페이지는 disabled=True
    st.page_link("pages/2_mapping_manager.py", label="🔗 매핑 매니저", disabled=True)
    #st.page_link("pages/3_unit_price_manager.py", label="💲 단가표 매니저", disabled=True)
    #st.page_link("pages/4_invoice_builder.py", label="🧾 청구서 빌더", disabled=True)

# ── 4) 간단 메트릭(예시) ─────────────────────────────
c1, c2, c3 = st.columns(3)
c1.metric("오늘 날짜", date.today().isoformat())
c2.metric("업로드된 파일", "—")
c3.metric("생성된 청구서", "—")

st.info("좌측 메뉴에서 페이지를 선택하면 해당 기능 화면으로 이동합니다.")
