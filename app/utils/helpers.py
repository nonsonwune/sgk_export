import qrcode
import io
import json
import logging
import base64
from io import BytesIO

logger = logging.getLogger(__name__)

def calculate_subtotal(shipment):
    """Calculate subtotal from all pricing components"""
    return sum([
        shipment.freight_pricing or 0,
        shipment.additional_charges or 0,
        shipment.pickup_charge or 0,
        shipment.handling_fees or 0,
        shipment.crating or 0,
        shipment.insurance_charge or 0
    ])

def calculate_vat(subtotal):
    """Calculate VAT (7% of subtotal)"""
    return subtotal * 0.07

def generate_qr_code(data, sender_mobile, receiver_mobile, order_booked_by):
    """Generate QR code and return as base64 string"""
    try:
        # Create QR code instance
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        
        # Add data
        qr.add_data(str(data))
        qr.make(fit=True)

        # Create image
        img = qr.make_image(fill_color="black", back_color="white")
        
        # Convert to base64
        buffered = BytesIO()
        img.save(buffered, format="PNG")
        img_str = base64.b64encode(buffered.getvalue()).decode()
        
        return f"data:image/png;base64,{img_str}"
    except Exception as e:
        logger.error(f"Error generating QR code: {str(e)}")
        return None 