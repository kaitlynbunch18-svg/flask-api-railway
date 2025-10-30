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
    init_db()     # Health check endpoints
    @app.get("/")
    def root():
        return {"status": "ok", "service": "flask-api"}, 200
    
    @app.get("/healthz")
    def healthz():
        return {"ok": True}, 200
    
    @app.get("/dbcheck")
    def dbcheck():
        from sqlalchemy import text
        from app.utils import engine
        try:
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            return {"db": "ok"}, 200
        except Exception as e:
            return {"db": "error", "message": str(e)}, 500

    return app
    return app

app = create_app()
