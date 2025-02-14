import logging
from datetime import datetime
import uuid
from sqlalchemy.types import TypeDecorator, CHAR
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql.type_api import TypeEngine
from ..extensions import db

logger = logging.getLogger(__name__)

class GUID(TypeDecorator):
    """Platform-independent GUID type.
    Uses PostgreSQL's UUID type, otherwise uses CHAR(36).
    """
    impl = CHAR
    cache_ok = True
    _isnull = False
    
    def __init__(self):
        super(GUID, self).__init__(length=36)
        self._is_uuid = True
        self._is_native = True

    @property
    def python_type(self):
        return uuid.UUID

    def load_dialect_impl(self, dialect):
        logger.debug(f"\n=== GUID load_dialect_impl ===")
        logger.debug(f"Dialect name: {dialect.name}")
        if dialect.name == 'postgresql':
            logger.debug("Using PostgreSQL UUID type")
            impl = dialect.type_descriptor(UUID(as_uuid=True))
            impl._is_uuid = True
            impl._isnull = False
            return impl
        logger.debug("Using CHAR type")
        impl = dialect.type_descriptor(CHAR(36))
        impl._is_uuid = True
        impl._isnull = False
        return impl

    def process_bind_param(self, value, dialect):
        """Process a value being bound as a parameter.
        Handles UUID conversion based on dialect type.
        """
        logger.debug(f"\n=== GUID BIND PARAM ===")
        logger.debug(f"Input value: {value}")
        logger.debug(f"Input type: {type(value)}")
        logger.debug(f"Dialect: {dialect.__class__.__name__ if dialect else 'None'}")
        
        if value is None:
            logger.debug("Returning None value")
            return value
            
        try:
            # Convert to UUID if not already
            if not isinstance(value, uuid.UUID):
                value = uuid.UUID(str(value))
                logger.debug(f"Converted to UUID: {value}")
            
            if dialect.name == 'postgresql':
                # For PostgreSQL, return UUID object directly
                logger.debug(f"PostgreSQL: Returning UUID object: {value}")
                return value
            else:
                # For other dialects, convert to string
                result = str(value)
                logger.debug(f"Other dialect: Converting to string: {result}")
                return result
        except Exception as e:
            logger.error(f"Error in process_bind_param: {str(e)}")
            raise

    def process_result_value(self, value, dialect):
        logger.debug(f"\n=== GUID RESULT VALUE ===")
        logger.debug(f"Input value: {value}")
        logger.debug(f"Input type: {type(value)}")
        logger.debug(f"Dialect: {dialect.name}")
        
        if value is None:
            logger.debug("Returning None value")
            return value
            
        try:
            if isinstance(value, uuid.UUID):
                logger.debug(f"Returning existing UUID: {value}")
                return value
                
            if dialect.name == 'postgresql':
                # PostgreSQL may return UUID or string
                if isinstance(value, str):
                    result = uuid.UUID(value)
                    logger.debug(f"PostgreSQL: Converted string to UUID: {result}")
                    return result
                return value
            else:
                # Other dialects will return string
                result = uuid.UUID(value)
                logger.debug(f"Other dialect: Converted to UUID: {result}")
                return result
        except Exception as e:
            logger.error(f"Error in process_result_value: {str(e)}")
            raise

    def coerce_compared_value(self, op, value):
        """Handle comparison operations between UUID types"""
        logger.debug(f"\n=== GUID coerce_compared_value ===")
        logger.debug(f"Operator: {op}, Value: {value}, Value type: {type(value)}")
        
        if value is None:
            return None
            
        # Get dialect if available
        dialect = getattr(op, 'dialect', None)
        logger.debug(f"Coercion dialect: {dialect.__class__.__name__ if dialect else 'None'}")
            
        try:
            # Return a new GUID type instance for proper comparison
            if isinstance(value, uuid.UUID):
                return self
                
            if isinstance(value, str):
                return self
                
            return self
        except (ValueError, AttributeError, TypeError) as e:
            logger.error(f"Error in coerce_compared_value: {str(e)}")
            raise

    def compare_values(self, x, y):
        """Implement comparison logic for UUID values"""
        logger.debug(f"\n=== GUID compare_values ===")
        logger.debug(f"Comparing x: {x} ({type(x)}) with y: {y} ({type(y)})")
        
        if x is None or y is None:
            return x is y
            
        # Convert both values to UUID for comparison
        try:
            x_uuid = x if isinstance(x, uuid.UUID) else uuid.UUID(str(x))
            y_uuid = y if isinstance(y, uuid.UUID) else uuid.UUID(str(y))
            return x_uuid == y_uuid
        except (ValueError, AttributeError, TypeError) as e:
            logger.error(f"Error comparing values: {str(e)}")
            return False

    def get_dbapi_type(self, dbapi):
        """Return the DBAPI type for UUID"""
        if hasattr(dbapi, 'UUID'):
            return dbapi.UUID
        return self.impl.get_dbapi_type(dbapi)

class ShipmentItem(db.Model):
    __tablename__ = 'item_detail'
    
    id = db.Column(GUID(), primary_key=True, default=uuid.uuid4)
    export_request_id = db.Column(GUID(), db.ForeignKey('export_request.id'), nullable=False)
    description = db.Column(db.String(200))
    value = db.Column(db.Float)
    quantity = db.Column(db.Integer)
    weight = db.Column(db.Float)
    image_filename = db.Column(db.String(255))
    image_file_id = db.Column(db.String(255))

class ShipmentStatusHistory(db.Model):
    __tablename__ = 'shipment_status_history'
    
    id = db.Column(GUID(), primary_key=True, default=uuid.uuid4)
    shipment_id = db.Column(GUID(), db.ForeignKey('export_request.id'), nullable=False)
    old_status = db.Column(db.String(50))
    new_status = db.Column(db.String(50), nullable=False)
    changed_by = db.Column(GUID(), db.ForeignKey('user.id'), nullable=False)
    changed_at = db.Column(db.DateTime(timezone=True), default=db.func.current_timestamp())
    
    # Relationships
    shipment = db.relationship('Shipment', backref=db.backref('status_history', lazy='dynamic', order_by='ShipmentStatusHistory.changed_at'))
    user = db.relationship('User', backref=db.backref('status_changes_made', lazy='dynamic'))

class Shipment(db.Model):
    __tablename__ = 'export_request'
    
    # Status Constants
    STATUS_PENDING = 'pending'
    STATUS_CONFIRMED = 'confirmed'
    STATUS_PROCESSING = 'processing'
    STATUS_IN_TRANSIT = 'in_transit'
    STATUS_DELIVERED = 'delivered'
    STATUS_CANCELLED = 'cancelled'
    STATUS_SAVED = 'saved'
    
    VALID_STATUSES = [
        STATUS_PENDING,
        STATUS_CONFIRMED,
        STATUS_PROCESSING,
        STATUS_IN_TRANSIT,
        STATUS_DELIVERED,
        STATUS_CANCELLED,
        STATUS_SAVED
    ]
    
    STATUS_TRANSITIONS = {
        STATUS_PENDING: [STATUS_CONFIRMED, STATUS_CANCELLED],
        STATUS_CONFIRMED: [STATUS_PROCESSING, STATUS_CANCELLED],
        STATUS_PROCESSING: [STATUS_IN_TRANSIT, STATUS_CANCELLED],
        STATUS_IN_TRANSIT: [STATUS_DELIVERED, STATUS_CANCELLED],
        STATUS_DELIVERED: [],  # No further transitions allowed
        STATUS_CANCELLED: [],  # No further transitions allowed
        STATUS_SAVED: [STATUS_PENDING, STATUS_CANCELLED]
    }
    
    id = db.Column(GUID(), primary_key=True, default=uuid.uuid4)
    waybill_number = db.Column(db.String(50), nullable=False)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    delivery_date = db.Column(db.DateTime)
    qr_code = db.Column(db.Text)
    
    # User relationship
    created_by = db.Column(GUID(), db.ForeignKey('user.id'), nullable=False, index=True)
    creator = db.relationship('User', 
                            backref=db.backref('shipments', lazy=True),
                            foreign_keys=[created_by])
    
    # Relationships
    items = db.relationship('ShipmentItem', backref='shipment', lazy=True, foreign_keys=[ShipmentItem.export_request_id])
    
    # Sender Information
    sender_name = db.Column(db.String(100), nullable=False)
    sender_email = db.Column(db.String(120))
    sender_address = db.Column(db.String(200))
    sender_business = db.Column(db.String(100))
    sender_mobile = db.Column(db.String(20), nullable=False)
    sender_signature = db.Column(db.Text)
    
    # Receiver Information
    receiver_name = db.Column(db.String(100), nullable=False)
    receiver_email = db.Column(db.String(120))
    receiver_address = db.Column(db.String(200))
    receiver_business = db.Column(db.String(100))
    receiver_mobile = db.Column(db.String(20), nullable=False)
    
    # Destination Details
    destination_address = db.Column(db.String(200))
    destination_country = db.Column(db.String(100))
    destination_postcode = db.Column(db.String(20))
    
    # Pricing Details
    freight_pricing = db.Column(db.Float, default=0)
    additional_charges = db.Column(db.Float, default=0)
    pickup_charge = db.Column(db.Float, default=0)
    handling_fees = db.Column(db.Float, default=0)
    crating = db.Column(db.Float, default=0)
    insurance_charge = db.Column(db.Float, default=0)
    total = db.Column(db.Float, default=0)
    
    # Additional Details
    is_collection = db.Column(db.Boolean, default=False)
    customer_group = db.Column(db.String(100))
    order_booked_by = db.Column(db.String(100))
    status = db.Column(db.String(50), default=STATUS_PENDING)
    
    # Status tracking fields
    status_changed_by = db.Column(GUID(), db.ForeignKey('user.id'), index=True)
    status_changed_at = db.Column(db.DateTime(timezone=True), default=db.func.current_timestamp())
    status_changer = db.relationship('User', 
                                   backref=db.backref('status_changes', lazy=True),
                                   foreign_keys=[status_changed_by])
    
    @property
    def calculated_total(self):
        """Calculate total from individual components"""
        return sum([
            self.freight_pricing or 0,
            self.additional_charges or 0,
            self.pickup_charge or 0,
            self.handling_fees or 0,
            self.crating or 0,
            self.insurance_charge or 0
        ])
    
    @classmethod
    def generate_waybill_number(cls):
        """Generate the next waybill number in sequence"""
        try:
            last_request = cls.query.order_by(cls.created_at.desc()).first()
            if not last_request:
                return 'EX000001'
            
            last_number = int(last_request.waybill_number[2:])
            next_number = last_number + 1
            return f'EX{next_number:06d}'
        except Exception as e:
            logger.error(f"Error generating waybill number: {str(e)}")
            raise 

    def can_transition_to(self, new_status):
        """Check if the shipment can transition to the given status"""
        return new_status in self.STATUS_TRANSITIONS.get(self.status, []) 

    def update_status(self, new_status, user_id):
        """Update shipment status with tracking information"""
        if self.can_transition_to(new_status):
            try:
                old_status = self.status
                self.status = new_status
                
                # Create status history entry
                history_entry = ShipmentStatusHistory(
                    shipment_id=self.id,
                    old_status=old_status,
                    new_status=new_status,
                    changed_by=user_id
                )
                db.session.add(history_entry)
                db.session.commit()
                return True
            except Exception as e:
                db.session.rollback()
                logger.error(f"Error updating shipment status: {str(e)}")
                raise
        return False 