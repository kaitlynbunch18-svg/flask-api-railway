from flask import Flask
from app.config import Config
from app.routes.products import bp as products_bp
from app.routes.workflows import bp as workflows_bp
from app.routes.webhooks import bp as webhooks_bp
from app.utils import init_db

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    # register blueprints
    app.register_blueprint(products_bp)
    app.register_blueprint(workflows_bp)
    app.register_blueprint(webhooks_bp)
    # init DB (idempotent)
    init_db()
    return app

app = create_app()
