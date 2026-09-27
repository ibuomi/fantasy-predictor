import os
from flask import Flask, send_from_directory
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


def create_app(test_config=None):
    base_dir = os.path.abspath(os.path.dirname(__file__))
    frontend_dist = os.path.join(base_dir, "..", "..", "frontend", "dist")

    app = Flask(__name__, static_folder=None)  # we serve the frontend manually below
    CORS(app)  # harmless in production; only matters if you run `npm run dev` separately

    default_db_path = os.path.join(base_dir, "..", "data", "fantasy.db")
    os.makedirs(os.path.dirname(default_db_path), exist_ok=True)

    app.config.from_mapping(
        SQLALCHEMY_DATABASE_URI=f"sqlite:///{default_db_path}",
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        SECRET_KEY="dev",
    )

    if test_config:
        app.config.update(test_config)

    db.init_app(app)

    from . import routes
    app.register_blueprint(routes.bp)

    with app.app_context():
        db.create_all()

    # Serve the built React app for every non-API route, so the whole thing
    # runs as a single process on a single port (`python run.py`) instead of
    # needing a separate `npm run dev` server. Falls back to index.html for
    # any path so React Router-style client-side routes still work if added
    # later. If frontend/dist doesn't exist yet (frontend never built),
    # this just 404s — see the README/start scripts, which build it first.
    @app.get("/", defaults={"path": ""})
    @app.get("/<path:path>")
    def serve_frontend(path):
        if path and os.path.exists(os.path.join(frontend_dist, path)):
            return send_from_directory(frontend_dist, path)
        index_path = os.path.join(frontend_dist, "index.html")
        if os.path.exists(index_path):
            return send_from_directory(frontend_dist, "index.html")
        return (
            "Frontend build not found. Run `npm run build` in the frontend/ "
            "folder first (or use start.ps1 / start.sh, which does this "
            "automatically).",
            404,
        )

    return app
