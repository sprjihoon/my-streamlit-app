# -*- coding: utf-8 -*-
"""templates/invoice_base.py – PDF Invoice Template
────────────────────────────────────────────────────
Shared template class (InvoicePDF) for all invoice‑related pages.
• ReportLab + NanumGothic 폰트 내장
• 한·영 다국어 지원 (lang='ko' | 'en')
• add_header / add_company_block / add_items_table / add_footer helpers

from templates.invoice_base import InvoicePDF

inv = InvoicePDF('invoice_240428.pdf', lang='ko')
inv.add_header('INV-2404-001', '2025-04-28')
inv.add_company_block(seller_dict, buyer_dict)
inv.add_items_table(items_list)  # [{desc, qty, unit_price}, ...]
inv.build()
"""

from __future__ import annotations

import os
from datetime import date
from typing import List, Dict

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Image,
    Table,
    TableStyle,
)
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

ASSETS_DIR = os.path.join(os.path.dirname(__file__), "..", "assets")
pdfmetrics.registerFont(
    TTFont("NanumGothic", os.path.join(ASSETS_DIR, "NanumGothic.ttf"))
)
pdfmetrics.registerFont(
    TTFont("NanumGothic-Bold", os.path.join(ASSETS_DIR, "NanumGothic-Bold.ttf"))
)


class InvoicePDF:
    """Lightweight builder class for 1‑page invoices."""

    def __init__(self, filename: str, lang: str = "ko"):
        self.filename = filename
        self.lang = lang  # 'ko' or 'en'
        self.buffer = []
        self._init_doc()
        self._init_styles()

    # ────────────────────────────────────
    # Internal helpers
    # ────────────────────────────────────
    def _init_doc(self):
        self.doc = SimpleDocTemplate(
            self.filename,
            pagesize=A4,
            leftMargin=18 * mm,
            rightMargin=18 * mm,
            topMargin=22 * mm,
            bottomMargin=18 * mm,
            title="Invoice",
        )

    def _init_styles(self):
        self.h1 = ParagraphStyle(
            "Heading1",
            fontName="NanumGothic-Bold",
            fontSize=18,
            leading=22,
            spaceAfter=6 * mm,
        )
        self.body = ParagraphStyle(
            "Body",
            fontName="NanumGothic",
            fontSize=10.5,
            leading=14,
        )
        self.tbl_hdr = ParagraphStyle(
            "TblHeader",
            fontName="NanumGothic-Bold",
            fontSize=9.5,
            leading=13,
        )

    # ────────────────────────────────────
    # Public builder API
    # ────────────────────────────────────
    def add_header(self, inv_no: str, inv_date: str | date):
        logo_path = os.path.join(ASSETS_DIR, "logo.png")
        logo = Image(logo_path, width=48 * mm, height=14 * mm)
        inv_date = inv_date if isinstance(inv_date, str) else inv_date.strftime("%Y-%m-%d")
        meta = Paragraph(
            f"""
            <para align=right>
            <b>{'청구서' if self.lang=='ko' else 'INVOICE'}</b><br/>
            No : {inv_no}<br/>
            Date : {inv_date}
            </para>
            """,
            self.body,
        )
        self.buffer.extend([
            Table([[logo, meta]], colWidths=[72 * mm, 90 * mm], style=[("VALIGN", (0, 0), (-1, -1), "TOP")]),
            Spacer(1, 6 * mm),
        ])

    def add_company_block(self, seller: Dict[str, str], buyer: Dict[str, str]):
        fmt = lambda d: "<br/>".join(d.values())
        t = Table(
            [
                [Paragraph("<b>From / 발행자</b>", self.tbl_hdr), Paragraph("<b>To / 수신자</b>", self.tbl_hdr)],
                [Paragraph(fmt(seller), self.body), Paragraph(fmt(buyer), self.body)],
            ],
            colWidths=[78 * mm, 78 * mm],
        )
        t.setStyle(
            TableStyle(
                [
                    ("BOX", (0, 0), (-1, -1), 0.4, "black"),
                    ("INNERGRID", (0, 0), (-1, -1), 0.4, "black"),
                    ("BACKGROUND", (0, 0), (-1, 0), "#F4F4F4"),
                ]
            )
        )
        self.buffer.extend([t, Spacer(1, 6 * mm)])

    def add_items_table(self, items: List[Dict]):
        header = ["번호", "항목", "수량", "단가", "금액"] if self.lang == "ko" else ["No", "Description", "Qty", "Unit", "Amount"]
        data = [header]
        total = 0
        for i, it in enumerate(items, 1):
            amt = it["qty"] * it["unit_price"]
            total += amt
            data.append([
                i,
                it["desc"],
                f"{it['qty']:,}",
                f"{it['unit_price']:,}",
                f"{amt:,}",
            ])
        data.append(["", "", "", "Subtotal", f"{total:,}"])
        tbl = Table(data, colWidths=[14 * mm, 72 * mm, 24 * mm, 32 * mm, 32 * mm])
        tbl.setStyle(
            TableStyle(
                [
                    ("FONTNAME", (0, 0), (-1, 0), "NanumGothic-Bold"),
                    ("BACKGROUND", (0, 0), (-1, 0), "#ECECEC"),
                    ("ALIGN", (2, 1), (-1, -1), "RIGHT"),
                    ("GRID", (0, 0), (-1, -2), 0.25, "#AAAAAA"),
                    ("BOX", (0, -1), (-1, -1), 0.6, "black"),
                    ("FONTNAME", (0, -1), (-1, -1), "NanumGothic-Bold"),
                ]
            )
        )
        self.buffer.append(tbl)
        return total

    def add_footer(self, note: str):
        self.buffer.extend([Spacer(1, 4 * mm), Paragraph(note, self.body)])

    def build(self):
        self.doc.build(self.buffer)
