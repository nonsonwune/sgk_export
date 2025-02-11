from flask import Blueprint, render_template, jsonify, request, current_app
from flask_login import login_required, current_user
from ..models.shipment import Shipment
from ..extensions import db
from sqlalchemy import desc
import logging
from sqlalchemy import case
from sqlalchemy import func

logger = logging.getLogger(__name__)

bp = Blueprint('profile', __name__, url_prefix='/profile')

@bp.route('/')
@login_required
def index():
    """Display user profile and shipment overview."""
    try:
        logger.debug("\n=== PROFILE PAGE ACCESS ===")
        logger.debug("User Authentication Info:")
        logger.debug(f"Authenticated User ID: {current_user.id}")
        logger.debug(f"User ID Type: {type(current_user.id)}")
        logger.debug(f"User Object Type: {type(current_user)}")
        logger.debug(f"User Dict: {current_user.__dict__}")
        
        # Verify database connection and get a sample shipment
        logger.debug("\n=== DATABASE VERIFICATION ===")
        try:
            sample_shipment = Shipment.query.first()
            if sample_shipment:
                logger.debug(f"Sample Shipment ID: {sample_shipment.id}")
                logger.debug(f"Sample Shipment created_by: {sample_shipment.created_by}")
                logger.debug(f"Sample Shipment created_by type: {type(sample_shipment.created_by)}")
            else:
                logger.debug("No shipments found in database")
        except Exception as e:
            logger.error(f"Database verification error: {str(e)}")

        # Debug raw shipment count with explicit type casting
        logger.debug("\n=== USER SHIPMENTS QUERY ===")
        user_id_str = str(current_user.id)
        logger.debug(f"Querying with user_id: {user_id_str}")
        
        # Try both with and without type casting for debugging
        count_with_cast = db.session.query(Shipment).filter(
            Shipment.created_by == str(current_user.id)
        ).count()
        count_without_cast = db.session.query(Shipment).filter(
            Shipment.created_by == current_user.id
        ).count()
        
        logger.debug(f"Count with string casting: {count_with_cast}")
        logger.debug(f"Count without string casting: {count_without_cast}")
        
        # Get all shipments for debugging
        logger.debug("\n=== ALL SHIPMENTS CHECK ===")
        all_shipments = Shipment.query.all()
        logger.debug(f"Total shipments in database: {len(all_shipments)}")
        for ship in all_shipments:
            logger.debug(f"Shipment ID: {ship.id}, created_by: {ship.created_by}, created_by type: {type(ship.created_by)}")
        
        # Original stats query with enhanced logging
        logger.debug("\n=== STATS QUERY ===")
        active_case = case(
            (Shipment.status.in_(['processing', 'in_transit']), 1),
            else_=0
        )
        
        stats_query = db.session.query(
            func.count(Shipment.id).label('total_shipments'),
            func.sum(Shipment.total).label('total_revenue'),
            func.sum(active_case).label('active_shipments'),
            func.sum(
                case(
                    (Shipment.status == 'delivered', 1),
                    else_=0
                )
            ).label('delivered_shipments')
        ).filter(Shipment.created_by == current_user.id)
        
        # Log the generated SQL
        logger.debug(f"Stats Query SQL: {stats_query.statement.compile(compile_kwargs={'literal_binds': True})}")
        
        stats = stats_query.first()
        logger.debug(f"Stats Query Result: {stats}")
        
        # Get status distribution with debug logging
        logger.debug("Querying status distribution")
        status_counts = db.session.query(
            Shipment.status,
            db.func.count(Shipment.id).label('count')
        ).filter(
            Shipment.created_by == current_user.id
        ).group_by(Shipment.status).all()
        
        logger.debug(f"Raw status counts: {status_counts}")

        # Format status counts with defaults
        status_distribution = {
            'pending': 0,
            'processing': 0,
            'in_transit': 0,
            'delivered': 0,
            'cancelled': 0
        }
        status_distribution.update({status: count for status, count in status_counts})
        
        logger.debug(f"Formatted status distribution: {status_distribution}")
        
        # Verify total counts match
        total_by_status = sum(status_distribution.values())
        logger.debug(f"Total by status distribution: {total_by_status}")
        logger.debug(f"Total by direct count: {count_without_cast}")
        if total_by_status != count_without_cast:
            logger.warning(f"Count mismatch: status distribution total ({total_by_status}) != direct count ({count_without_cast})")
        
        # Get recent shipments with debug logging
        logger.debug("Querying recent shipments")
        recent_shipments = Shipment.query.filter(
            Shipment.created_by == current_user.id
        ).order_by(db.desc(Shipment.created_at)).limit(5).all()
        
        logger.debug(f"Retrieved {len(recent_shipments)} recent shipments")
        for shipment in recent_shipments:
            logger.debug(f"Shipment {shipment.waybill_number}: Status={shipment.status}, Created by={shipment.created_by}")

        return render_template('profile/index.html',
                             user=current_user,
                             stats=stats,
                             status_distribution=status_distribution,
                             recent_shipments=recent_shipments)
    except Exception as e:
        logger.error(f"Error in profile index: {str(e)}", exc_info=True)
        return render_template('error.html', error="Failed to load profile data"), 500

@bp.route('/shipments')
@login_required
def shipments():
    """Display user's shipments with filtering and pagination."""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        status = request.args.get('status')
        search = request.args.get('search')

        # Base query
        query = Shipment.query.filter_by(created_by=current_user.id)

        # Apply filters
        if status:
            query = query.filter(Shipment.status == status)
        if search:
            search_term = f"%{search}%"
            query = query.filter(
                db.or_(
                    Shipment.waybill_number.ilike(search_term),
                    Shipment.sender_name.ilike(search_term),
                    Shipment.receiver_name.ilike(search_term),
                    Shipment.destination_address.ilike(search_term)
                )
            )

        # Execute query with pagination
        pagination = query.order_by(desc(Shipment.created_at)).paginate(
            page=page, per_page=per_page, error_out=False
        )

        return render_template('profile/shipments.html',
                             shipments=pagination.items,
                             pagination=pagination,
                             status=status,
                             search=search)
    except Exception as e:
        logger.error(f"Error in profile shipments: {str(e)}")
        return render_template('error.html', error="Failed to load shipments data"), 500

@bp.route('/api/shipments')
@login_required
def get_shipments():
    """API endpoint for user's shipments data."""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        status = request.args.get('status')
        search = request.args.get('search')

        query = Shipment.query.filter_by(created_by=current_user.id)

        if status:
            query = query.filter(Shipment.status == status)
        if search:
            search_term = f"%{search}%"
            query = query.filter(
                db.or_(
                    Shipment.waybill_number.ilike(search_term),
                    Shipment.sender_name.ilike(search_term),
                    Shipment.receiver_name.ilike(search_term),
                    Shipment.destination_address.ilike(search_term)
                )
            )

        total = query.count()
        shipments = query.order_by(desc(Shipment.created_at)).limit(per_page).offset((page - 1) * per_page).all()

        return jsonify({
            'shipments': [s.to_dict() for s in shipments],
            'total': total,
            'page': page,
            'per_page': per_page,
            'total_pages': (total + per_page - 1) // per_page
        })
    except Exception as e:
        logger.error(f"Error in get shipments API: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500 