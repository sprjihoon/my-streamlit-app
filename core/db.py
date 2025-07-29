"""
new_cal/core/db.py
──────────────────
SQLite 연결 헬퍼.
다른 모듈에서 `from .db import get_conn` 으로 호출합니다.
"""
import sqlite3, os
from contextlib import contextmanager

DB_PATH = os.getenv("BILLING_DB", "new_cal/data/billing.db")
os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

@contextmanager
def get_conn():
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    try:
        yield con
    finally:
        con.close()
