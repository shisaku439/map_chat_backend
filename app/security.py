from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, Callable, Dict, Optional, Tuple

import jwt
from flask import current_app, jsonify, request
from werkzeug.security import check_password_hash, generate_password_hash


def create_password_hash(password: str) -> str:
    # 一部環境で hashlib.scrypt が無いため、方式をPBKDF2に固定
    return generate_password_hash(password, method="pbkdf2:sha256")


def verify_password(password_hash: str, password: str) -> bool:
    return check_password_hash(password_hash, password)


def create_jwt(user_id: int, username: str, expires_in_days: int = 7) -> Tuple[str, int]:
    now = datetime.now(timezone.utc)
    exp = now + timedelta(days=expires_in_days)
    payload = {
        "sub": user_id,
        "username": username,
        "iat": int(now.timestamp()),
        "exp": int(exp.timestamp()),
    }
    # SECRET_KEY を安全に取得（str/bytes以外や空はフォールバック）
    key = current_app.config.get("SECRET_KEY")
    signing_key = key if (isinstance(key, (str, bytes)) and key) else "dev-secret-key"
    token = jwt.encode(payload, signing_key, algorithm="HS256")
    return token, int(exp.timestamp() * 1000)


def decode_jwt(token: str) -> Dict[str, Any]:
    key = current_app.config.get("SECRET_KEY")
    signing_key = key if (isinstance(key, (str, bytes)) and key) else "dev-secret-key"
    return jwt.decode(  # type: ignore[no-any-return]
        token,
        signing_key,
        algorithms=["HS256"],
    )


def json_error(status: int, code: str, message: str):
    return jsonify({"error": {"code": code, "message": message}}), status


def get_bearer_token(req) -> Optional[str]:
    auth = req.headers.get("Authorization", "")
    if not auth.startswith("Bearer "):
        return None
    return auth.split(" ", 1)[1]


def require_auth(fn: Callable[..., Any]) -> Callable[..., Any]:
    def wrapper(*args, **kwargs):
        token = get_bearer_token(request)
        if not token:
            return json_error(401, "UNAUTHORIZED", "認証が必要です")
        try:
            payload = decode_jwt(token)
        except jwt.ExpiredSignatureError:
            return json_error(401, "TOKEN_EXPIRED", "トークンの有効期限が切れています")
        except jwt.InvalidTokenError:
            return json_error(401, "INVALID_TOKEN", "トークンが不正です")
        request.user = {  # type: ignore[attr-defined]
            "id": payload.get("sub"),
            "username": payload.get("username"),
        }
        return fn(*args, **kwargs)

    wrapper.__name__ = fn.__name__
    return wrapper
