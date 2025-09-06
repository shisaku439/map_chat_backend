from __future__ import annotations

from flask import Flask
from flask_cors import CORS
from flask_migrate import Migrate
from flask_socketio import SocketIO
from .config import load_config
from .models import db

socketio = SocketIO()
migrate = Migrate()


def create_app() -> Flask:
    app = Flask(__name__)
    # 設定を読み込み
    load_config(app)

    # 拡張初期化
    CORS(app, resources={r"/*": {"origins": [app.config["FRONT_ORIGIN"]]}})
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

    return app
