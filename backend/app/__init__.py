from flask import Flask
from .config import Config
from .extensions import db, migrate


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)
    migrate.init_app(app, db)
    
    with app.app_context():
        from . import models
        from .routes import auth_bp, messages_bp, receipts_bp
        
        app.register_blueprint(auth_bp)
        app.register_blueprint(messages_bp)
        app.register_blueprint(receipts_bp)

    return app
