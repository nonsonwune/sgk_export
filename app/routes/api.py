from flask import Blueprint, jsonify, request, current_app
from flask_login import login_required, current_user
from ..models.shipment import Shipment, ShipmentItem
from ..utils.helpers import calculate_subtotal, calculate_vat
from ..extensions import db
from sqlalchemy import func, case
import logging
from datetime import datetime
from functools import wraps
import jwt

logger = logging.getLogger(__name__)

bp = Blueprint('api', __name__, url_prefix='/api')

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization')
        
        if not token:
            return jsonify({'message': 'Token is missing'}), 401
        
        try:
            if not token.startswith('Bearer '):
                raise jwt.InvalidTokenError('Invalid token format')
            
            token = token.split(' ')[1]
            data = jwt.decode(token, current_app.config['SECRET_KEY'], algorithms=['HS256'])
            
            # Add additional token validation if needed
            
        except jwt.ExpiredSignatureError:
            return jsonify({'message': 'Token has expired'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'message': 'Invalid token'}), 401
        
        return f(*args, **kwargs)
    return decorated

@bp.route('/shipments', methods=['GET'])
@token_required
def list_shipments():
    logger.debug('API: Accessing shipments list')
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        status = request.args.get('status')
        search = request.args.get('search')
        
        query = Shipment.query
        
        if status:
            query = query.filter(Shipment.status == status)
            
        if search:
            search_term = f'%{search}%'
            query = query.filter(
                db.or_(
                    Shipment.waybill_number.ilike(search_term),
                    Shipment.sender_name.ilike(search_term),
                    Shipment.receiver_name.ilike(search_term),
                    Shipment.destination.ilike(search_term)
                )
            )
        
        total = query.count()
        
        shipments = query.order_by(Shipment.created_at.desc()) \
                        .limit(per_page).offset((page - 1) * per_page).all()
        
        return jsonify({
            'shipments': [s.to_dict() for s in shipments],
            'total': total,
            'page': page,
            'per_page': per_page,
            'total_pages': (total + per_page - 1) // per_page
        })
    except Exception as e:
        logger.error(f'API Error in list_shipments: {str(e)}')
        return jsonify({'error': 'Internal server error'}), 500

@bp.route('/shipments/<int:shipment_id>', methods=['GET'])
@token_required
def get_shipment(shipment_id):
    logger.debug(f'API: Accessing shipment details for ID: {shipment_id}')
    try:
        shipment = Shipment.query.get_or_404(shipment_id)
        return jsonify(shipment.to_dict(include_items=True))
    except Exception as e:
        logger.error(f'API Error in get_shipment {shipment_id}: {str(e)}')
        return jsonify({'error': 'Internal server error'}), 500

@bp.route('/shipments', methods=['POST'])
@token_required
def create_shipment():
    logger.debug('API: Creating new shipment')
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
            
        required_fields = [
            'sender_name', 'sender_email', 'sender_mobile', 'sender_address',
            'receiver_name', 'receiver_email', 'receiver_mobile', 'receiver_address',
            'destination'
        ]
        
        missing_fields = [field for field in required_fields if field not in data]
        if missing_fields:
            return jsonify({
                'error': 'Missing required fields',
                'fields': missing_fields
            }), 400
        
        # Calculate pricing
        subtotal = calculate_subtotal(
            float(data.get('shipping_cost', 0)),
            float(data.get('insurance_cost', 0)),
            float(data.get('packaging_cost', 0)),
            float(data.get('other_charges', 0))
        )
        vat = calculate_vat(subtotal)
        total = subtotal + vat
        
        # Create shipment
        shipment = Shipment(
            sender_name=data['sender_name'],
            sender_email=data['sender_email'],
            sender_mobile=data['sender_mobile'],
            sender_business=data.get('sender_business'),
            sender_address=data['sender_address'],
            receiver_name=data['receiver_name'],
            receiver_email=data['receiver_email'],
            receiver_mobile=data['receiver_mobile'],
            receiver_business=data.get('receiver_business'),
            receiver_address=data['receiver_address'],
            destination=data['destination'],
            shipping_cost=float(data.get('shipping_cost', 0)),
            insurance_cost=float(data.get('insurance_cost', 0)),
            packaging_cost=float(data.get('packaging_cost', 0)),
            other_charges=float(data.get('other_charges', 0)),
            subtotal=subtotal,
            vat=vat,
            total=total,
            customer_group=data.get('customer_group', 'regular'),
            notes=data.get('notes'),
            created_by=current_user.id if current_user.is_authenticated else None
        )
        
        db.session.add(shipment)
        db.session.flush()  # Get shipment ID without committing
        
        # Process items
        items = data.get('items', [])
        for item_data in items:
            if all(k in item_data for k in ['description', 'value', 'quantity', 'weight']):
                item = ShipmentItem(
                    shipment_id=shipment.id,
                    description=item_data['description'],
                    value=float(item_data['value']),
                    quantity=int(item_data['quantity']),
                    weight=float(item_data['weight'])
                )
                db.session.add(item)
        
        db.session.commit()
        return jsonify(shipment.to_dict(include_items=True)), 201
        
    except ValueError as e:
        db.session.rollback()
        logger.error(f'API Error in create_shipment (validation): {str(e)}')
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        db.session.rollback()
        logger.error(f'API Error in create_shipment: {str(e)}')
        return jsonify({'error': 'Internal server error'}), 500

@bp.route('/shipments/<int:shipment_id>', methods=['PUT'])
@token_required
def update_shipment(shipment_id):
    logger.debug(f'API: Updating shipment {shipment_id}')
    try:
        shipment = Shipment.query.get_or_404(shipment_id)
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        # Update shipment details
        for field in [
            'sender_name', 'sender_email', 'sender_mobile', 'sender_business', 'sender_address',
            'receiver_name', 'receiver_email', 'receiver_mobile', 'receiver_business', 'receiver_address',
            'destination', 'customer_group', 'notes'
        ]:
            if field in data:
                setattr(shipment, field, data[field])
        
        # Update costs if provided
        if any(field in data for field in ['shipping_cost', 'insurance_cost', 'packaging_cost', 'other_charges']):
            shipment.shipping_cost = float(data.get('shipping_cost', shipment.shipping_cost))
            shipment.insurance_cost = float(data.get('insurance_cost', shipment.insurance_cost))
            shipment.packaging_cost = float(data.get('packaging_cost', shipment.packaging_cost))
            shipment.other_charges = float(data.get('other_charges', shipment.other_charges))
            
            # Recalculate totals
            shipment.subtotal = calculate_subtotal(
                shipment.shipping_cost,
                shipment.insurance_cost,
                shipment.packaging_cost,
                shipment.other_charges
            )
            shipment.vat = calculate_vat(shipment.subtotal)
            shipment.total = shipment.subtotal + shipment.vat
        
        # Update items if provided
        if 'items' in data:
            # Remove existing items
            for item in shipment.items:
                db.session.delete(item)
            
            # Add new items
            for item_data in data['items']:
                if all(k in item_data for k in ['description', 'value', 'quantity', 'weight']):
                    item = ShipmentItem(
                        shipment_id=shipment.id,
                        description=item_data['description'],
                        value=float(item_data['value']),
                        quantity=int(item_data['quantity']),
                        weight=float(item_data['weight'])
                    )
                    db.session.add(item)
        
        db.session.commit()
        return jsonify(shipment.to_dict(include_items=True))
        
    except ValueError as e:
        db.session.rollback()
        logger.error(f'API Error in update_shipment (validation): {str(e)}')
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        db.session.rollback()
        logger.error(f'API Error in update_shipment: {str(e)}')
        return jsonify({'error': 'Internal server error'}), 500

@bp.route('/shipments/<int:shipment_id>', methods=['DELETE'])
@token_required
def delete_shipment(shipment_id):
    logger.debug(f'API: Deleting shipment {shipment_id}')
    try:
        shipment = Shipment.query.get_or_404(shipment_id)
        db.session.delete(shipment)
        db.session.commit()
        return '', 204
    except Exception as e:
        db.session.rollback()
        logger.error(f'API Error in delete_shipment: {str(e)}')
        return jsonify({'error': 'Internal server error'}), 500

@bp.route('/shipments/<int:shipment_id>/status', methods=['PATCH'])
@token_required
def update_status(shipment_id):
    logger.debug(f'API: Updating status for shipment {shipment_id}')
    try:
        shipment = Shipment.query.get_or_404(shipment_id)
        data = request.get_json()
        
        if not data or 'status' not in data:
            return jsonify({'error': 'Status not provided'}), 400
            
        new_status = data['status']
        if new_status not in ['pending', 'in_transit', 'delivered', 'cancelled']:
            return jsonify({'error': 'Invalid status value'}), 400
            
        shipment.status = new_status
        db.session.commit()
        
        return jsonify({'status': shipment.status})
    except Exception as e:
        db.session.rollback()
        logger.error(f'API Error in update_status: {str(e)}')
        return jsonify({'error': 'Internal server error'}), 500

@bp.route('/stats', methods=['GET'])
@token_required
def get_stats():
    logger.debug('API: Accessing statistics')
    try:
        # Get date range from query parameters or use current month
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        if start_date:
            start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
        else:
            start_date = datetime.now().date().replace(day=1)
            
        if end_date:
            end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
        else:
            end_date = datetime.now().date()
        
        # Get statistics
        stats = db.session.query(
            func.count(Shipment.id).label('total_shipments'),
            func.sum(Shipment.total).label('total_revenue'),
            func.avg(Shipment.total).label('average_revenue'),
            func.sum(Shipment.vat).label('total_vat'),
            func.count(case([(Shipment.status == 'delivered', 1)])).label('delivered_shipments'),
            func.count(case([(Shipment.status == 'cancelled', 1)])).label('cancelled_shipments')
        ).filter(
            Shipment.created_at.between(start_date, end_date)
        ).first()
        
        # Get status distribution
        status_distribution = db.session.query(
            Shipment.status,
            func.count(Shipment.id).label('count')
        ).filter(
            Shipment.created_at.between(start_date, end_date)
        ).group_by(
            Shipment.status
        ).all()
        
        # Get customer group distribution
        customer_distribution = db.session.query(
            Shipment.customer_group,
            func.count(Shipment.id).label('count'),
            func.sum(Shipment.total).label('revenue')
        ).filter(
            Shipment.created_at.between(start_date, end_date)
        ).group_by(
            Shipment.customer_group
        ).all()
        
        return jsonify({
            'period': {
                'start_date': start_date.isoformat(),
                'end_date': end_date.isoformat()
            },
            'summary': {
                'total_shipments': stats.total_shipments or 0,
                'total_revenue': float(stats.total_revenue or 0),
                'average_revenue': float(stats.average_revenue or 0),
                'total_vat': float(stats.total_vat or 0),
                'delivered_shipments': stats.delivered_shipments or 0,
                'cancelled_shipments': stats.cancelled_shipments or 0
            },
            'status_distribution': {
                status: count for status, count in status_distribution
            },
            'customer_distribution': [{
                'group': group,
                'count': count,
                'revenue': float(revenue or 0)
            } for group, count, revenue in customer_distribution]
        })
    except Exception as e:
        logger.error(f'API Error in get_stats: {str(e)}')
        return jsonify({'error': 'Internal server error'}), 500 