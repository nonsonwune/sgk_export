from flask import Blueprint, render_template, jsonify, request
from ..models.shipment import Shipment
from ..extensions import db
import logging

logger = logging.getLogger(__name__)

bp = Blueprint('tracking', __name__, url_prefix='/track')

@bp.route('/', methods=['GET'])
def tracking_page():
    """Display the tracking search page."""
    return render_template('tracking/search.html')

@bp.route('/<waybill>', methods=['GET'])
def track_shipment(waybill):
    """Display tracking information for a shipment."""
    logger.debug(f'Tracking shipment with waybill: {waybill}')
    try:
        shipment = Shipment.query.filter_by(waybill_number=waybill).first_or_404()
        
        # Get limited shipment details for public viewing
        tracking_info = {
            'waybill_number': shipment.waybill_number,
            'status': shipment.status,
            'created_at': shipment.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            'destination': shipment.destination,
            'sender': {
                'name': shipment.sender_name,
                'business': shipment.sender_business
            },
            'receiver': {
                'name': shipment.receiver_name,
                'business': shipment.receiver_business
            },
            'items': [{
                'description': item.description,
                'quantity': item.quantity
            } for item in shipment.items]
        }
        
        return render_template('tracking/details.html', 
                             tracking_info=tracking_info,
                             shipment=shipment)
    except Exception as e:
        logger.error(f'Error tracking shipment {waybill}: {str(e)}')
        return render_template('tracking/error.html', waybill=waybill)

@bp.route('/api/search', methods=['POST'])
def search_shipment():
    """API endpoint for tracking search."""
    logger.debug('Processing tracking search request')
    try:
        data = request.get_json()
        if not data or 'waybill' not in data:
            return jsonify({'error': 'Waybill number not provided'}), 400
            
        waybill = data['waybill']
        shipment = Shipment.query.filter_by(waybill_number=waybill).first()
        
        if not shipment:
            return jsonify({
                'found': False,
                'message': 'Shipment not found'
            })
        
        return jsonify({
            'found': True,
            'tracking_url': f'/track/{waybill}'
        })
    except Exception as e:
        logger.error(f'Error in tracking search: {str(e)}')
        return jsonify({'error': 'Internal server error'}), 500

@bp.route('/api/<waybill>', methods=['GET'])
def get_tracking_info(waybill):
    """API endpoint for tracking information."""
    logger.debug(f'API: Tracking shipment with waybill: {waybill}')
    try:
        shipment = Shipment.query.filter_by(waybill_number=waybill).first_or_404()
        
        tracking_info = {
            'waybill_number': shipment.waybill_number,
            'status': shipment.status,
            'created_at': shipment.created_at.isoformat(),
            'destination': shipment.destination,
            'sender': {
                'name': shipment.sender_name,
                'business': shipment.sender_business
            },
            'receiver': {
                'name': shipment.receiver_name,
                'business': shipment.receiver_business
            },
            'items': [{
                'description': item.description,
                'quantity': item.quantity
            } for item in shipment.items],
            'qr_code': shipment.qr_code if shipment.qr_code else None
        }
        
        return jsonify(tracking_info)
    except Exception as e:
        logger.error(f'API Error in tracking info {waybill}: {str(e)}')
        return jsonify({'error': 'Internal server error'}), 500 