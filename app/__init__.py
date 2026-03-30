"""
MIT-WPU Vyas Smart-Room Maintenance Tracker
Flask Application Factory
"""
import os
import secrets
import logging
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from dotenv import load_dotenv
from .socket_events import init_socketio

# SocketIO instance (will be initialized in create_app)
socketio = None

# Load environment variables from .env file
load_dotenv()

logger = logging.getLogger(__name__)
db = SQLAlchemy()


def create_app(config_name=None):
    """Application factory pattern for creating Flask app."""
    app = Flask(__name__, 
                template_folder='templates',
                static_folder='static')
    
    # Configuration — all secrets come from .env
    secret_key = os.environ.get('SECRET_KEY')
    if not secret_key:
        secret_key = secrets.token_hex(32)
        logger.warning(
            'SECRET_KEY is not set in environment. A temporary random key has been generated. '
            'Sessions will not persist across server restarts. Set SECRET_KEY in your .env file.'
        )
    app.config['SECRET_KEY'] = secret_key
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get(
        'DATABASE_URL', 'sqlite:///vyas_tracker.db'
    )
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['UPLOAD_FOLDER'] = os.path.join(app.root_path, 'static', 'uploads')
    app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
    
    # Ensure upload directory exists
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    
    # Initialize extensions
    db.init_app(app)
    
    # Initialize SocketIO
    global socketio
    socketio = init_socketio(app)
    
    # Register blueprints
    from .blueprints.main import main_bp
    from .blueprints.admin import admin_bp
    from .blueprints.auth import auth_bp
    from .blueprints.professional import professional_bp
    from .blueprints.superadmin import superadmin_bp
    
    app.register_blueprint(main_bp)
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(auth_bp)
    app.register_blueprint(professional_bp)
    app.register_blueprint(superadmin_bp)
    
    # Initialize database and run migrations
    from .database import init_db
    init_db(app)
    
    # Register Jinja filters
    @app.template_filter('ist')
    def format_ist(value, format='%b %d, %H:%M'):
        if value is None:
            return ""
        from datetime import timedelta
        # UTC to IST is +5:30
        ist_time = value + timedelta(hours=5, minutes=30)
        return ist_time.strftime(format)
    
    return app
