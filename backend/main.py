"""FastAPI app for DiffSense AI.

Run after installing optional dependency fastapi/uvicorn:
    uvicorn app.main:app --reload --app-dir backend
"""

from __future__ import annotations

from typing import Any

try:
    from fastapi import FastAPI, HTTPException
    from pydantic import BaseModel, Field
except Exception:  # pragma: no cover - lets CLI/tests run without web deps
    FastAPI = None
    HTTPException = Exception
    BaseModel = object
    Field = None

from .analyzer import analyze_pr, review_pr


if FastAPI is not None:
    app = FastAPI(title="DiffSense AI", version="0.1.0")

    class AnalyzeRequest(BaseModel):
        pr_url: str

    class ReviewRequest(BaseModel):
        pr_url: str | None = Field(default=None, alias="prUrl")

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.post("/api/analyze")
    def analyze(req: AnalyzeRequest) -> dict[str, Any]:
        return analyze_pr(req.pr_url)

    @app.post("/api/review")
    def review(req: ReviewRequest) -> dict[str, Any]:
        pr_url = req.pr_url
        if not pr_url:
            raise HTTPException(status_code=400, detail="prUrl is required")
        try:
            return review_pr(pr_url)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        except RuntimeError as exc:
            raise HTTPException(status_code=502, detail=str(exc)) from exc
else:
    app = None
