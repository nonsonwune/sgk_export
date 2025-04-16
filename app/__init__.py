print("Starting package load: app/__init__.py")
import os
import sys
import logging
from flask import Flask, render_template, flash
from .extensions import db, login_manager, migrate, csrf
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
        migrate.init_app(app, db)
        login_manager.init_app(app)
        csrf.init_app(app)
        logger.debug("Extensions initialized")
    except Exception as e:
        logger.error(f"Failed to initialize extensions: {str(e)}", exc_info=True)
        raise
    
    # CSRF and HTTP 400 Error Handler
    @app.errorhandler(400)
    def handle_csrf_error(e):
        # Check if this is a CSRF error
        if 'CSRF' in str(e) or hasattr(e, 'description') and 'CSRF' in str(e.description):
            logger.error(f"CSRF Error: {str(e)}")
            flash("CSRF validation failed. Please try again.", "error")
            return render_template('error.html', error="Security validation failed. Please try again."), 400
        
        # Handle other 400 errors
        logger.error(f"400 Error: {str(e)}")
        return render_template('error.html', error=f"Bad request: {str(e)}"), 400
    
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
    
    # Configure CSRF to accept tokens from headers (after blueprints are registered)
    from .extensions import configure_csrf
    configure_csrf(app)
    
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