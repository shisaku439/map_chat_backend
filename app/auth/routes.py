from __future__ import annotations

import re
from flask import Blueprint, jsonify, request
from ..models import db
from ..models.user import User
from ..security import (
    create_jwt,
    create_password_hash,
    json_error,
    require_auth,
    verify_password,
)


auth_bp = Blueprint("auth", __name__)

USERNAME_RE = re.compile(r"^[a-zA-Z0-9_]{3,20}$")


@auth_bp.post("/register")
def register():  # type: ignore[no-redef]
    body = request.get_json(silent=True) or {}
    username = str(body.get("username", "")).strip()
    password = str(body.get("password", ""))

    if not USERNAME_RE.match(username):
        return json_error(400, "VALIDATION_ERROR", "ユーザー名は3〜20文字の半角英数と_のみです")
    if not (8 <= len(password) <= 64):
        return json_error(400, "VALIDATION_ERROR", "パスワードは8〜64文字で入力してください")

    exists = User.query.filter_by(username=username).first()
    if exists:
        return json_error(409, "USERNAME_CONFLICT", "このユーザー名はすでに使用されています")

    user = User(username=username, password_hash=create_password_hash(password))
    db.session.add(user)
    db.session.commit()

    token, expires_at = create_jwt(user.id, user.username)
    return (
        jsonify(
            {
                "userId": user.id,
                "username": user.username,
                "token": token,
                "expiresAt": expires_at,
            }
        ),
        201,
    )


@auth_bp.post("/login")
def login():  # type: ignore[no-redef]
    body = request.get_json(silent=True) or {}
    username = str(body.get("username", "")).strip()
    password = str(body.get("password", ""))

    if not USERNAME_RE.match(username):
        return json_error(400, "VALIDATION_ERROR", "ユーザー名は3〜20文字の半角英数と_のみです")
    if not (8 <= len(password) <= 64):
        return json_error(400, "VALIDATION_ERROR", "パスワードは8〜64文字で入力してください")

    user = User.query.filter_by(username=username).first()
    if not user or not verify_password(user.password_hash, password):
        return json_error(401, "INVALID_CREDENTIALS", "ユーザー名またはパスワードが違います")

    token, expires_at = create_jwt(user.id, user.username)
    return jsonify(
        {
            "userId": user.id,
            "username": user.username,
            "token": token,
            "expiresAt": expires_at,
        }
    )


@auth_bp.get("/me")
@require_auth
def me():  # type: ignore[no-redef]
    user = request.user  # type: ignore[attr-defined]
    return jsonify({"userId": user["id"], "username": user["username"]})


@auth_bp.post("/logout")
def logout():  # type: ignore[no-redef]
    return ("", 204)
