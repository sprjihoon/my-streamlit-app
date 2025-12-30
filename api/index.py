"""
Vercel Serverless Function - FastAPI Backend
"""
import sys
import os

# 경로 설정
root_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, root_path)

# 환경변수 설정
os.environ.setdefault("BILLING_DB", "/tmp/billing.db")
os.environ.setdefault("DATABASE_PATH", "/tmp/billing.db")

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# 라우터 임포트
from backend.app.api import (
    health_router, 
    calculate_router, 
    upload_router, 
    vendors_router, 
    rates_router, 
    insights_router, 
    invoices_router, 
    auth_router, 
    logs_router
)

# FastAPI 앱 생성
app = FastAPI(
    title="Billing API",
    description="인보이스 계산 및 관리 API",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 라우터 등록
app.include_router(health_router)
app.include_router(calculate_router)
app.include_router(upload_router)
app.include_router(vendors_router)
app.include_router(rates_router)
app.include_router(insights_router)
app.include_router(invoices_router)
app.include_router(auth_router)
app.include_router(logs_router)


@app.get("/")
async def root():
    """API 루트."""
    return {
        "name": "Billing API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health",
    }


@app.on_event("startup")
async def startup_event():
    """앱 시작 시 DB 테이블 확인."""
    try:
        from logic import ensure_tables
        ensure_tables()
    except Exception as e:
        print(f"DB init error: {e}")


# Vercel 핸들러
handler = app
