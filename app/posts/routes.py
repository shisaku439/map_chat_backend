from __future__ import annotations

from flask import Blueprint, jsonify, request
from typing import List
import math
from datetime import timezone

from ..models import db
from ..models.post import Post
from ..security import json_error, require_auth
from .. import socketio


posts_bp = Blueprint("posts", __name__)


def _is_valid_lat_lng(lat: float, lng: float) -> bool:
    return -90.0 <= lat <= 90.0 and -180.0 <= lng <= 180.0


def _haversine_m(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """2点間の地表距離（メートル）。"""
    R = 6371000.0
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlmb = math.radians(lng2 - lng1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlmb / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c


@posts_bp.post("")
@require_auth
def create_post():  # type: ignore[no-redef]
    body = request.get_json(silent=True) or {}
    message = str(body.get("message", "")).strip()
    lat = body.get("lat", None)
    lng = body.get("lng", None)

    if not message:
        return json_error(400, "VALIDATION_ERROR", "メッセージは必須です")
    if len(message) > 280:
        return json_error(400, "VALIDATION_ERROR", "メッセージは280文字以内で入力してください")

    try:
        lat_f = float(lat)
        lng_f = float(lng)
    except (TypeError, ValueError):
        return json_error(400, "VALIDATION_ERROR", "緯度経度が不正です")

    if not _is_valid_lat_lng(lat_f, lng_f):
        return json_error(400, "VALIDATION_ERROR", "緯度経度が範囲外です")

    user = request.user  # type: ignore[attr-defined]
    post = Post(user_id=int(user["id"]), message=message, lat=lat_f, lng=lng_f)
    db.session.add(post)
    db.session.commit()

    payload = {
        "id": post.id,
        "userId": post.user_id,
        "message": post.message,
        "lat": post.lat,
        "lng": post.lng,
        "createdAt": post.created_at.replace(tzinfo=timezone.utc).isoformat().replace("+00:00", "Z"),
    }
    # リアルタイム配信（全体ブロードキャスト）
    socketio.emit("post_created", payload)

    return (
        jsonify(payload),
        201,
    )


@posts_bp.get("")
def list_nearby():  # type: ignore[no-redef]
    """現在地周辺の投稿を半径で絞り込み。

    Query params:
      - lat, lng: 現在地（必須）
      - radius: 半径メートル（100〜3000, 既定300）
    """
    try:
        lat = float(request.args.get("lat", ""))
        lng = float(request.args.get("lng", ""))
    except ValueError:
        return json_error(400, "VALIDATION_ERROR", "lat/lngが不正です")

    if not _is_valid_lat_lng(lat, lng):
        return json_error(400, "VALIDATION_ERROR", "緯度経度が範囲外です")

    try:
        radius = int(request.args.get("radius", "1000"))
    except ValueError:
        radius = 300
    # 半径は100〜3000mに制限
    radius = max(100, min(3000, radius))

    # おおよそのバウンディングボックスで一次絞り込み
    # 1度あたりのメートル換算（緯度固定）
    meters_per_deg_lat = 111_000.0
    meters_per_deg_lng = 111_000.0 * math.cos(math.radians(lat))
    dlat = radius / meters_per_deg_lat
    dlng = radius / max(1e-6, meters_per_deg_lng)

    min_lat = lat - dlat
    max_lat = lat + dlat
    min_lng = lng - dlng
    max_lng = lng + dlng

    q = (
        Post.query.filter(Post.lat >= min_lat, Post.lat <= max_lat, Post.lng >= min_lng, Post.lng <= max_lng)
        .order_by(Post.created_at.desc())
        .limit(300)
    )
    rows: List[Post] = q.all()

    items = []
    for p in rows:
        dist = _haversine_m(lat, lng, float(p.lat), float(p.lng))
        if dist <= radius:
            items.append(
                {
                    "id": p.id,
                    "userId": p.user_id,
                    "message": p.message,
                    "lat": p.lat,
                    "lng": p.lng,
                    "createdAt": p.created_at.replace(tzinfo=timezone.utc).isoformat().replace("+00:00", "Z"),
                    "distance": int(dist),
                }
            )

    # 近い順に揃える
    items.sort(key=lambda x: x["distance"])  # type: ignore[index]
    return jsonify({"items": items, "center": {"lat": lat, "lng": lng}, "radius": radius})
