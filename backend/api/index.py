"""Vercel serverless entry point for ZKONER API."""
import os
import sys
import traceback
from pathlib import Path

# Ensure backend dir is on sys.path
_backend_dir = str(Path(__file__).resolve().parent.parent)
if _backend_dir not in sys.path:
    sys.path.insert(0, _backend_dir)

# Ensure data directory exists
os.makedirs(os.path.join(_backend_dir, "data"), exist_ok=True)

# Try to import and capture any error
try:
    from main import app
except Exception as e:
    # Log the error
    error_msg = f"Import failed: {e}\n{traceback.format_exc()}"
    print(error_msg, file=sys.stderr)
    # Create a fallback app that returns the error
    from fastapi import FastAPI
    from fastapi.responses import JSONResponse

    fallback_app = FastAPI()

    @fallback_app.route("/{path:path}")
    async def error_handler(path: str):
        return JSONResponse(
            status_code=500,
            content={"error": "Backend import failed", "detail": str(e)}
        )

    app = fallback_app
