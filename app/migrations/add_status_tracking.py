"""Add status tracking fields to shipments table

This migration adds fields to track who changes a shipment's status and when.
"""

from flask import current_app
from ..extensions import db
import logging

logger = logging.getLogger(__name__)

def upgrade():
    """Add status tracking columns"""
    try:
        with current_app.app_context():
            db.session.execute("""
                ALTER TABLE export_request 
                ADD COLUMN status_changed_by UUID REFERENCES "user"(id),
                ADD COLUMN status_changed_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP;

                CREATE INDEX idx_shipment_status_tracking 
                ON export_request(status_changed_by, status_changed_at);

                COMMENT ON COLUMN export_request.status_changed_by IS 'References the user who last changed the shipment status';
                COMMENT ON COLUMN export_request.status_changed_at IS 'Timestamp when the shipment status was last changed';
            """)
            db.session.commit()
            logger.info("Successfully added status tracking columns")
    except Exception as e:
        logger.error(f"Error adding status tracking columns: {str(e)}")
        db.session.rollback()
        raise

def downgrade():
    """Remove status tracking columns"""
    try:
        with current_app.app_context():
            db.session.execute("""
                DROP INDEX IF EXISTS idx_shipment_status_tracking;
                ALTER TABLE export_request 
                DROP COLUMN IF EXISTS status_changed_by,
                DROP COLUMN IF EXISTS status_changed_at;
            """)
            db.session.commit()
            logger.info("Successfully removed status tracking columns")
    except Exception as e:
        logger.error(f"Error removing status tracking columns: {str(e)}")
        db.session.rollback()
        raise 