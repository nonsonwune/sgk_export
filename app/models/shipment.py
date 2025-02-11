import logging
from datetime import datetime
import uuid
from sqlalchemy.types import TypeDecorator, CHAR
from sqlalchemy.dialects.postgresql import UUID
from ..extensions import db

logger = logging.getLogger(__name__)

class GUID(TypeDecorator):
    """Platform-independent GUID type.
    Uses PostgreSQL's UUID type, otherwise uses CHAR(36), storing as stringified hex values.
    """
    impl = CHAR
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == 'postgresql':
            return dialect.type_descriptor(UUID())
        else:
            return dialect.type_descriptor(CHAR(36))

    def process_bind_param(self, value, dialect):
        logger.debug(f"\n=== GUID BIND PARAM ===")
        logger.debug(f"Input value: {value}")
        logger.debug(f"Input type: {type(value)}")
        logger.debug(f"Dialect: {dialect.name}")
        
        if value is None:
            logger.debug("Returning None value")
            return value
        elif dialect.name == 'postgresql':
            result = str(value)
            logger.debug(f"PostgreSQL: Converting to string: {result}")
            return result
        else:
            if not isinstance(value, uuid.UUID):
                result = str(uuid.UUID(value))
                logger.debug(f"Non-UUID input: Converting to UUID string: {result}")
                return result
            else:
                result = str(value)
                logger.debug(f"UUID input: Converting to string: {result}")
                return result

    def process_result_value(self, value, dialect):
        logger.debug(f"\n=== GUID RESULT VALUE ===")
        logger.debug(f"Input value: {value}")
        logger.debug(f"Input type: {type(value)}")
        logger.debug(f"Dialect: {dialect.name}")
        
        if value is None:
            logger.debug("Returning None value")
            return value
        else:
            if not isinstance(value, uuid.UUID):
                result = uuid.UUID(value)
                logger.debug(f"Non-UUID input: Converting to UUID: {result}")
                return result
            else:
                logger.debug(f"Returning UUID value: {value}")
                return value

class ShipmentItem(db.Model):
    __tablename__ = 'item_detail'
    
    id = db.Column(GUID(), primary_key=True, default=lambda: str(uuid.uuid4()))
    export_request_id = db.Column(GUID(), db.ForeignKey('export_request.id'), nullable=False)
    description = db.Column(db.String(200))
    value = db.Column(db.Float)
    quantity = db.Column(db.Integer)
    weight = db.Column(db.Float)
    image_filename = db.Column(db.String(255))
    image_file_id = db.Column(db.String(255))

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
    
    id = db.Column(GUID(), primary_key=True, default=lambda: str(uuid.uuid4()))
    waybill_number = db.Column(db.String(50), nullable=False)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    delivery_date = db.Column(db.DateTime)
    qr_code = db.Column(db.Text)
    
    # User relationship
    created_by = db.Column(GUID(), db.ForeignKey('user.id'), nullable=False, index=True)
    creator = db.relationship('User', backref=db.backref('shipments', lazy=True))
    
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