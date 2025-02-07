print("Starting module load: wsgi.py")
import logging
import sys
from app import create_app

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

logger.debug(f"Python path in wsgi.py: {sys.path}")
logger.debug("Module name: %s", __name__)
logger.debug("Starting Flask application initialization in WSGI")

try:
    application = create_app()
    app = application  # For Gunicorn compatibility
    logger.debug("Flask application initialized successfully in WSGI")
    logger.debug("App variable type: %s", type(app))
    logger.debug("App variable attributes: %s", dir(app))
except Exception as e:
    logger.error("Failed to initialize Flask application in WSGI: %s", str(e), exc_info=True)
    raise

if __name__ == '__main__':
    app.run() 