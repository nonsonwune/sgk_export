from flask import current_app
from app import create_app
from app.migrations.migrate_user_ids import migrate_user_ids
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def run_migration():
    """Run the migration within Flask application context"""
    app = create_app()
    with app.app_context():
        logger.info("Starting migration within application context")
        success = migrate_user_ids()
        if success:
            logger.info("Migration completed successfully")
        else:
            logger.error("Migration failed - will need to use SQL backup plan")
            
if __name__ == '__main__':
    run_migration() 