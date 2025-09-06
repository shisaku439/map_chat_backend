from __future__ import annotations
import os

# eventletワーカー使用時は、最初期にモンキーパッチを適用して
# 標準ライブラリ(threading/socket等)との不整合を防ぐ
import eventlet

eventlet.monkey_patch()

from app import create_app, socketio  # noqa: E402

app = create_app()

if __name__ == "__main__":
    socketio.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 5001)))
