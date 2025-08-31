from __future__ import annotations

import os
import sqlite3
from pathlib import Path

from flask import Flask
from flask_socketio import SocketIO, emit
from flask_cors import CORS


app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-secret-key")

# 開発中はCORSを広めに許可。運用時はフロントのオリジンに限定すること。
FRONT_ORIGIN = os.environ.get("FRONT_ORIGIN", "http://localhost:5174")
CORS(app, resources={r"/*": {"origins": [FRONT_ORIGIN]}})
socketio = SocketIO(app, cors_allowed_origins=[FRONT_ORIGIN])

DB_PATH = Path(__file__).resolve().parent / "db.sqlite3"


def get_db() -> sqlite3.Connection:
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def init_db() -> None:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    connection = get_db()
    cursor = connection.cursor()

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL
        );
        """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS posts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            message TEXT NOT NULL,
            lat REAL NOT NULL,
            lng REAL NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(user_id) REFERENCES users(id)
        );
        """
    )

    connection.commit()
    connection.close()


@app.get("/health")
def health() -> tuple[dict[str, str], int]:
    return {"status": "ok"}, 200


@app.get("/api/hello")
def hello() -> tuple[dict[str, str], int]:
    return {"message": "hello from backend"}, 200


@socketio.on("connect")
def handle_connect():  # type: ignore[no-redef]
    emit("server_message", {"message": "connected"})


@socketio.on("ping")
def handle_ping(data):  # type: ignore[no-redef]
    emit("pong", {"ok": True, "echo": data})


if __name__ == "__main__":
    init_db()
    socketio.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
