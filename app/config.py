from __future__ import annotations

import os
from pathlib import Path
from flask import Flask
from dotenv import load_dotenv


def load_config(app: Flask) -> None:

    load_dotenv(Path(__file__).resolve().parents[1] / ".env")

    app.config.setdefault("SECRET_KEY", os.environ.get("SECRET_KEY", "dev-secret-key"))
    app.config.setdefault("FRONT_ORIGIN", os.environ.get("FRONT_ORIGIN", "http://localhost:5173"))
    # SQLite（相対パス: backend/db.sqlite3）
    db_path = Path(__file__).resolve().parents[1] / "db.sqlite3"
    app.config.setdefault("SQLALCHEMY_DATABASE_URI", f"sqlite:///{db_path}")
    app.config.setdefault("SQLALCHEMY_TRACK_MODIFICATIONS", False)
