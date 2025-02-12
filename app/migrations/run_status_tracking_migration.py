"""Run the status tracking migration

This script runs the migration to add status tracking fields to the shipments table.
"""

from flask import Flask
from ..extensions import db
from . import add_status_tracking
import logging

logger = logging.getLogger(__name__)

def run_migration(app):
    """Run the status tracking migration"""
    try:
        with app.app_context():
            logger.info("Starting status tracking migration")
            add_status_tracking.upgrade()
            logger.info("Status tracking migration completed successfully")
    except Exception as e:
        logger.error(f"Error running status tracking migration: {str(e)}")
        raise

if __name__ == '__main__':
    from .. import create_app
    app = create_app()
    run_migration(app) 