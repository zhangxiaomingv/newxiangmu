"""ZKONER API — AI Brand Visibility & Growth Diagnostic System.

Usage:
    uvicorn main:app --reload --port 8000
"""

import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.storage import init_db
from app.routers.analysis import router as analysis_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(
    title="ZKONER API",
    description="AI Brand Visibility & Growth Diagnostic System",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS — allow dev origins + production frontend + custom (for Railway)
_CORS_ORIGINS = os.getenv("CORS_ORIGINS", "")
_extra_origins = [o.strip() for o in _CORS_ORIGINS.split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "https://zkoner.com",
        "https://www.zkoner.com",
        *_extra_origins,
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(analysis_router, prefix="/api")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
