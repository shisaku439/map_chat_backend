from __future__ import annotations

from flask import Flask
from flask_cors import CORS
from flask_migrate import Migrate
from flask_socketio import SocketIO
from .config import load_config
from .models import db

socketio = SocketIO(async_mode="gevent")
migrate = Migrate()


def create_app() -> Flask:
    app = Flask(__name__)
    # 設定を読み込み
    load_config(app)

    # 拡張初期化
    CORS(app, resources={r"/*": {"origins": [app.config["FRONT_ORIGIN"]]}})
    # DB接続の安定化: pool_pre_ping 有効化
    app.config.setdefault("SQLALCHEMY_ENGINE_OPTIONS", {"pool_pre_ping": True})
    db.init_app(app)
    migrate.init_app(app, db)
    socketio.init_app(app, cors_allowed_origins=[app.config["FRONT_ORIGIN"]])

    # ルート/Blueprint登録
    from .routes.api import api_bp
    from .auth.routes import auth_bp
    from .posts.routes import posts_bp

    app.register_blueprint(api_bp)
    app.register_blueprint(auth_bp, url_prefix="/api/auth")
    app.register_blueprint(posts_bp, url_prefix="/api/posts")

    # ソケットイベント登録
    from .sockets.handlers import register_socket_handlers

    register_socket_handlers(socketio)

    # 起動時に自動マイグレーション（Shell無しでも整合を取る）
    from sqlalchemy import inspect

    try:
        from flask_migrate import upgrade, stamp

        with app.app_context():
            try:
                upgrade()
            except Exception:
                # 失敗時: 最低限のスキーマを作成してヘッドにスタンプ
                db.create_all()
                try:
                    stamp("head")
                except Exception:
                    pass
            # 念のため存在確認。無ければ作成→スタンプ
            inspector = inspect(db.engine)
            if not inspector.has_table("users") or not inspector.has_table("posts"):
                db.create_all()
                try:
                    stamp("head")
                except Exception:
                    pass
    except Exception:
        # flask_migrateが利用できない環境でも最低限のスキーマを用意
        with app.app_context():
            inspector = inspect(db.engine)
            if not inspector.has_table("users") or not inspector.has_table("posts"):
                db.create_all()

    return app
