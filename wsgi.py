from __future__ import annotations
import os
from app import create_app, socketio

app = create_app()

if __name__ == "__main__":
    socketio.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 5001)))
