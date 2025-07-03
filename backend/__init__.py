import os
from flask import Flask, send_from_directory
from .models import db
from .routes import bp


def create_app():
    """Factory to create and configure the Flask app."""
    app = Flask(__name__, static_folder='../frontend', static_url_path='')
    app.config['SQLALCHEMY_DATABASE_URI'] = (
        os.getenv('DATABASE_URL', 'sqlite:///arivu.db')
    )
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    db.init_app(app)
    app.register_blueprint(bp)
    
    # Serve frontend
    @app.route('/')
    def index():
        return send_from_directory(app.static_folder, 'index.html')
    
    # Create tables if they don't exist
    with app.app_context():
        db.create_all()
    
    return app

