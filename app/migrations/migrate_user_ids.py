import uuid
import logging
from sqlalchemy import text
from ..extensions import db
from ..models.user import User
from ..models.shipment import Shipment

logger = logging.getLogger(__name__)

def is_valid_uuid(val):
    """Check if string is a valid UUID"""
    try:
        uuid.UUID(str(val))
        return True
    except (ValueError, AttributeError):
        return False

def backup_tables():
    """Create backup of users and shipments tables"""
    try:
        logger.info("Creating backup tables...")
        db.session.execute(text("CREATE TABLE users_backup AS SELECT * FROM user"))
        db.session.execute(text("CREATE TABLE shipments_backup AS SELECT * FROM export_request"))
        db.session.commit()
        logger.info("Backup tables created successfully")
        return True
    except Exception as e:
        logger.error(f"Backup failed: {str(e)}")
        db.session.rollback()
        return False

def migrate_user_ids():
    """Migrate numeric IDs to UUIDs"""
    logger.info("Starting user ID migration...")
    
    # Create backup first
    if not backup_tables():
        logger.error("Backup failed, aborting migration")
        return False
    
    try:
        # Get all users
        users = User.query.all()
        logger.info(f"Found {len(users)} users to process")
        
        # Store old ID to new ID mapping
        id_mapping = {}
        
        # Update users
        for user in users:
            logger.debug(f"Processing user: {user.id}")
            if not is_valid_uuid(user.id):
                old_id = user.id
                new_id = str(uuid.uuid4())
                logger.info(f"Converting user ID: {old_id} -> {new_id}")
                
                # Store mapping
                id_mapping[old_id] = new_id
                
                # Update user ID
                user.id = new_id
        
        # First flush to ensure user IDs are updated
        db.session.flush()
        logger.info("User IDs updated successfully")
        
        # Update shipments
        for old_id, new_id in id_mapping.items():
            logger.debug(f"Updating shipments for user {old_id} -> {new_id}")
            affected_rows = Shipment.query.filter_by(created_by=old_id).update(
                {'created_by': new_id}
            )
            logger.info(f"Updated {affected_rows} shipments for user {old_id}")
        
        # Commit all changes
        db.session.commit()
        logger.info("Migration completed successfully")
        
        # Verify migration
        verify_migration(id_mapping)
        
        return True
        
    except Exception as e:
        logger.error(f"Migration failed: {str(e)}")
        db.session.rollback()
        return False

def verify_migration(id_mapping):
    """Verify the migration was successful"""
    logger.info("Verifying migration...")
    
    try:
        # Check all user IDs are valid UUIDs
        invalid_users = [user for user in User.query.all() if not is_valid_uuid(user.id)]
        if invalid_users:
            logger.error(f"Found {len(invalid_users)} users with invalid UUIDs")
            for user in invalid_users:
                logger.error(f"Invalid user ID: {user.id}")
        else:
            logger.info("All user IDs are valid UUIDs")
        
        # Check shipment associations
        for old_id, new_id in id_mapping.items():
            shipments = Shipment.query.filter_by(created_by=old_id).all()
            if shipments:
                logger.error(f"Found {len(shipments)} shipments still using old ID: {old_id}")
            
            shipments = Shipment.query.filter_by(created_by=new_id).all()
            logger.info(f"Found {len(shipments)} shipments with new ID: {new_id}")
            
    except Exception as e:
        logger.error(f"Verification failed: {str(e)}")

def rollback_migration():
    """Rollback to backup tables if needed"""
    try:
        logger.info("Rolling back migration...")
        db.session.execute(text("DROP TABLE user"))
        db.session.execute(text("ALTER TABLE users_backup RENAME TO user"))
        db.session.execute(text("DROP TABLE export_request"))
        db.session.execute(text("ALTER TABLE shipments_backup RENAME TO export_request"))
        db.session.commit()
        logger.info("Rollback completed successfully")
        return True
    except Exception as e:
        logger.error(f"Rollback failed: {str(e)}")
        return False

if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    success = migrate_user_ids()
    if not success:
        logger.error("Migration failed, attempting rollback...")
        if rollback_migration():
            logger.info("Rollback successful")
        else:
            logger.error("Rollback failed, manual intervention required") 