from flask_login import LoginManager
from .models.user import User
import logging

logger = logging.getLogger(__name__)

login_manager = LoginManager()

@login_manager.user_loader
def load_user(user_id):
    """Load user by ID with UUID validation"""
    logger.debug(f"Loading user with ID: {user_id}")
    
    # Validate UUID format
    if not User.is_valid_uuid(user_id):
        logger.error(f"Invalid UUID format: {user_id}")
        return None
    
    try:
        user = User.query.get(str(user_id))
        if user:
            logger.debug(f"Found user: {user.username}")
            return user
        else:
            logger.error(f"No user found with ID: {user_id}")
            return None
    except Exception as e:
        logger.error(f"Error loading user: {str(e)}")
        return None

@login_manager.unauthorized_handler
def unauthorized():
    """Handle unauthorized access attempts"""
    logger.warning("Unauthorized access attempt")
    return "You must be logged in to access this content.", 401 