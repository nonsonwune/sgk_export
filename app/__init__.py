print("Starting package load: app/__init__.py")
import os
import sys
import logging
from flask import Flask
from .extensions import db, login_manager
from .models.user import User
from .utils.logging_config import setup_logging
from .config import config
from uuid import UUID

logger = logging.getLogger(__name__)

def create_app(config_name=None):
    """Application factory function"""
    logger.debug("Starting application initialization")
    logger.debug(f"Python path during create_app: {sys.path}")
    logger.debug(f"Current working directory: {os.getcwd()}")
    
    if not config_name:
        config_name = os.environ.get('FLASK_ENV', 'development')
    logger.debug(f"Using configuration: {config_name}")
    
    # Initialize Flask app with explicit template folder
    template_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), 'templates'))
    static_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), 'static'))
    app = Flask(__name__, template_folder=template_dir, static_folder=static_dir)
    logger.debug(f"Template directory set to: {template_dir}")
    logger.debug("Flask app instance created")
    
    # Load configuration
    try:
        app.config.from_object(config[config_name])
        logger.debug("Configuration loaded successfully")
        logger.debug(f"Loaded config values: {dict(app.config)}")
    except Exception as e:
        logger.error(f"Failed to load configuration: {str(e)}", exc_info=True)
        raise
    
    # Set up logging
    try:
        setup_logging()
        logger.debug("Logging configured")
    except Exception as e:
        logger.error(f"Failed to setup logging: {str(e)}", exc_info=True)
        raise
    
    # Initialize extensions
    try:
        logger.debug("Initializing extensions")
        db.init_app(app)
        login_manager.init_app(app)
        logger.debug("Extensions initialized")
    except Exception as e:
        logger.error(f"Failed to initialize extensions: {str(e)}", exc_info=True)
        raise
    
    # Register blueprints
    try:
        logger.debug("Registering blueprints")
        from .routes import main, auth, shipments, tracking, contacts, admin, api, profile
        app.register_blueprint(main.bp)
        app.register_blueprint(auth.bp)
        app.register_blueprint(shipments.bp)
        app.register_blueprint(tracking.bp)
        app.register_blueprint(contacts.bp)
        app.register_blueprint(admin.bp)
        app.register_blueprint(api.bp)
        app.register_blueprint(profile.bp)
        logger.debug("Blueprints registered")
    except Exception as e:
        logger.error(f"Failed to register blueprints: {str(e)}", exc_info=True)
        raise
    
    # User loader callback
    @login_manager.user_loader
    def load_user(user_id):
        try:
            # Attempt to convert the user_id to UUID
            uuid_id = UUID(user_id)
            return db.session.get(User, uuid_id)
        except (ValueError, TypeError):
            # If the user_id is not a valid UUID, return None
            # This will cause Flask-Login to treat the user as not authenticated
            return None
    
    logger.debug("Application initialization completed")
    logger.debug(f"Final app object type: {type(app)}")
    logger.debug(f"Final app object attributes: {dir(app)}")
    return app 