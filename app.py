print("Starting module load: app.py")
import sys
import logging
from app import create_app

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

logger.debug(f"Python path: {sys.path}")
logger.debug("Module name: %s", __name__)
logger.debug("Starting Flask application initialization")

try:
    app = create_app()
    logger.debug("Flask application initialized successfully")
    logger.debug("App variable type: %s", type(app))
    logger.debug("App variable attributes: %s", dir(app))
except Exception as e:
    logger.error("Failed to initialize Flask application: %s", str(e), exc_info=True)
    raise

if __name__ == '__main__':
    app.run() 