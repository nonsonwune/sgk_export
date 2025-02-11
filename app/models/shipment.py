import logging
from datetime import datetime
import uuid
from ..extensions import db

logger = logging.getLogger(__name__)

class ShipmentItem(db.Model):
    __tablename__ = 'item_detail'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    export_request_id = db.Column(db.String(36), db.ForeignKey('export_request.id'), nullable=False)
    description = db.Column(db.String(200))
    value = db.Column(db.Float)
    quantity = db.Column(db.Integer)
    weight = db.Column(db.Float)
    image_filename = db.Column(db.String(255))
    image_file_id = db.Column(db.String(255))

class Shipment(db.Model):
    __tablename__ = 'export_request'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    waybill_number = db.Column(db.String(50), nullable=False)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    delivery_date = db.Column(db.DateTime)
    qr_code = db.Column(db.Text)
    
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
    status = db.Column(db.String(50), default='draft')
    
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