from __future__ import annotations

from flask import Blueprint

api_bp = Blueprint("api", __name__)


@api_bp.get("/health")
def health():  # type: ignore[no-redef]
    return {"status": "ok"}, 200


@api_bp.get("/api/hello")
def hello():  # type: ignore[no-redef]
    return {"message": "hello from backend"}, 200
