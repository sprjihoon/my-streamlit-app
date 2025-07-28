# pages/zzz_invoice_demo.py
# ───────────────────────────────────────────────
import io
import datetime as dt
import streamlit as st
from templates.invoice_base import InvoicePDF

st.set_page_config(page_title="Invoice Demo", layout="centered")
st.title("📄 Invoice Template 데모")

# ───────────────────────────────────────────────
# 1) 데모용 데이터
# ───────────────────────────────────────────────
SELLER = {
    "Company": "Spring Fulfillment",
    "Address": "Daegu, Korea",
    "Tel": "+82-53-123-4567",
}
BUYER = {
    "Company": "Test Buyer",
    "Address": "Seoul, Korea",
    "Tel": "010-0000-0000",
}
ITEMS = [
    dict(desc="기본 출고비", qty=13_000, unit_price=900),
    dict(desc="택배 요금 (극소)", qty=12_000, unit_price=2_100),
    dict(desc="PP봉투", qty=2_500, unit_price=70),
]

# ───────────────────────────────────────────────
# 2) PDF 생성 버튼
# ───────────────────────────────────────────────
if st.button("🖨️ PDF 생성"):
    buf = io.BytesIO()
    file_name = f"invoice_{dt.datetime.now():%Y%m%d_%H%M%S}.pdf"

    # PDF 작성
    pdf = InvoicePDF(buf, lang="ko")                # 'en' 으로 바꾸면 영어 레이아웃
    pdf.add_header("INV-TEST-001", dt.date.today())
    pdf.add_company_block(SELLER, BUYER)
    pdf.add_items_table(ITEMS)
    pdf.add_footer("※ 본 서식은 데모 용도로만 사용됩니다.")
    pdf.build()
    buf.seek(0)

    # 다운로드 버튼
    st.download_button(
        "📥 PDF 다운로드",
        buf,
        file_name=file_name,
        mime="application/pdf",
    )
    st.success("✅ PDF가 준비되었습니다!")
