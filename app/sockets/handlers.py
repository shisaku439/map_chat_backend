from __future__ import annotations

from flask_socketio import SocketIO, emit


def register_socket_handlers(socketio: SocketIO) -> None:
    @socketio.on("connect")
    def handle_connect():  # type: ignore[no-redef]
        emit("server_message", {"message": "connected"})

    @socketio.on("ping")
    def handle_ping(data):  # type: ignore[no-redef]
        emit("pong", {"ok": True, "echo": data})
