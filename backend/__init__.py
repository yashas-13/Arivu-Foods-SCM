import os
from flask import Flask, send_from_directory
from .models import db
from .routes import bp


def create_app():
    """Factory to create and configure the Flask app."""
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = (
        os.getenv('DATABASE_URL', 'sqlite:///arivu.db')
    )
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    db.init_app(app)
    app.register_blueprint(bp)
    
    # Serve static files from frontend directory
    @app.route('/')
    def serve_frontend():
        return send_from_directory('../frontend', 'index.html')
    
    @app.route('/<path:filename>')
    def serve_static(filename):
        return send_from_directory('../frontend', filename)
    
    # Create database tables
    with app.app_context():
        db.create_all()
    
    return app

