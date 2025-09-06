from __future__ import annotations
import os
import sys

# ローカルで `python wsgi.py` 実行時のみ eventlet を適用。
# 本番（Gunicorn + gevent ワーカー）では eventlet を読み込まない。
if __name__ == "__main__":
    # eventletワーカー使用時は最初期にモンキーパッチ
    import eventlet  # noqa: WPS433 (local import by design)

    if sys.platform == "darwin":
        try:
            import eventlet.hubs  # noqa: WPS433

            eventlet.hubs.use_hub("selects")
        except Exception:  # noqa: BLE001
            pass
    eventlet.monkey_patch()

from app import create_app, socketio  # noqa: E402

app = create_app()

if __name__ == "__main__":
    socketio.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 5001)))
