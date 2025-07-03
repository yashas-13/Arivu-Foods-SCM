import os
from flask import Flask
from .models import db
from .routes import bp


def create_app():
    """Factory to create and configure the Flask app."""
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = (
        os.getenv('DATABASE_URL', 'sqlite:///arivu.db')
    )
    db.init_app(app)
    app.register_blueprint(bp)
    return app

