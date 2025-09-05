from __future__ import annotations

from flask_sqlalchemy import SQLAlchemy


db = SQLAlchemy()

# Ensure models are imported so SQLAlchemy can resolve relationship strings
from .user import User  # noqa: E402,F401
from .post import Post  # noqa: E402,F401
