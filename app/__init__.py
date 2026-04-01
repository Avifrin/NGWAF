from flask import Flask
from .config import Config
from .extensions import db, redis_client
from .models import RequestLog, HoneypotEvent

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)
    redis_client.init_app(app)

    with app.app_context():
        db.create_all()

    from .waf.router import waf_bp, waf_middleware
    from .dashboard.views import dashboard_bp
    from .honeypot.views import honeypot_bp
    from .main.views import main_bp

    app.register_blueprint(waf_bp)
    app.register_blueprint(dashboard_bp, url_prefix="/dashboard")
    app.register_blueprint(honeypot_bp, url_prefix="/honeypot")
    app.register_blueprint(main_bp)

    return app
