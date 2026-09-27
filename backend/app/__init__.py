import os
from flask import Flask
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


def create_app(test_config=None):
    app = Flask(__name__)
    CORS(app)  # frontend runs on a different port during dev

    base_dir = os.path.abspath(os.path.dirname(__file__))
    default_db_path = os.path.join(base_dir, "..", "fantasy.db")

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

    return app
