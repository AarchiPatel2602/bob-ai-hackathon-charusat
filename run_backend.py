"""
RouteWise AI — Backend Runner
Launches the FastAPI backend server on port 8000.
"""

import os
import sys

# Ensure src in Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "src")))
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

import uvicorn

if __name__ == "__main__":
    print("[RouteWise AI] Starting FastAPI Control Tower backend on http://127.0.0.1:8000 ...")
    uvicorn.run("backend.app.main:app", host="127.0.0.1", port=8000, reload=True)
