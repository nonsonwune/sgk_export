from flask import Blueprint, render_template, redirect, url_for, request, flash, current_app, send_from_directory
from flask_login import login_required, current_user
from ..models.shipment import Shipment
from ..extensions import db
from sqlalchemy import func, case
import logging
from datetime import datetime, timedelta
import os
from appwrite.client import Client
from ..utils.appwrite import init_appwrite

logger = logging.getLogger(__name__)

bp = Blueprint('main', __name__)

@bp.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    return redirect(url_for('auth.login'))

@bp.route('/dashboard')
@login_required
def dashboard():
    """Dashboard view function"""
    try:
        logger.debug("Starting dashboard view function")
        logger.debug("Checking available endpoints")
        logger.debug(f"Current registered blueprints: {[bp.name for bp in current_app.blueprints.values()]}")
        logger.debug(f"Current registered view functions: {list(current_app.view_functions.keys())}")
        
        logger.debug("Checking database schema")
        logger.debug(f"Available columns in export_request table: {[c.name for c in Shipment.__table__.columns]}")
        
        logger.debug("Fetching recent shipments for dashboard")
        recent_shipments = Shipment.query.order_by(
            Shipment.created_at.desc()
        ).limit(5).all()
        
        # Get statistics
        total_shipments = Shipment.query.count()
        pending_shipments = Shipment.query.filter_by(status='pending').count()
        completed_shipments = Shipment.query.filter_by(status='completed').count()
        
        return render_template('dashboard.html',
                             recent_shipments=recent_shipments,
                             total_shipments=total_shipments,
                             pending_shipments=pending_shipments,
                             completed_shipments=completed_shipments)
                             
    except Exception as e:
        logger.error(f"Error loading dashboard: {str(e)}", exc_info=True)
        flash('An error occurred while loading the dashboard.', 'error')
        return render_template('error.html', error=str(e)), 500

@bp.route('/profile')
@login_required
def profile():
    """Display user profile with recent shipments and statistics"""
    logger.debug('Accessing user profile')
    try:
        # Get recent shipments (no user filtering)
        logger.debug('Fetching recent shipments')
        recent_shipments = Shipment.query.order_by(
            Shipment.created_at.desc()
        ).limit(10).all()
        logger.debug(f'Found {len(recent_shipments)} recent shipments')
        
        # Get overall statistics
        logger.debug('Calculating shipment statistics')
        shipment_stats = db.session.query(
            func.count(Shipment.id).label('total_shipments'),
            func.sum(Shipment.total).label('total_revenue'),
            func.count(case((Shipment.status == 'delivered', 1))).label('delivered_shipments')
        ).first()
        logger.debug('Statistics calculated successfully')
        
        return render_template('profile.html',
                             recent_shipments=recent_shipments,
                             user_stats=shipment_stats)
    except Exception as e:
        logger.error(f'Error loading user profile: {str(e)}', exc_info=True)
        flash('An error occurred while loading the profile.', 'error')
        return render_template('error.html', error=str(e)), 500

@bp.route('/print_form_template')
@login_required
def print_form_template():
    """Render the print form template."""
    try:
        current_app.logger.debug("Accessing print form template")
        current_app.logger.debug(f"Current user ID: {current_user.id}")
        
        current_app.logger.debug("Attempting to query all shipments")
        shipments = Shipment.query.all()
        current_app.logger.debug(f"Found {len(shipments)} shipments")
        
        selected_shipment = None
        shipment_id = request.args.get('shipment_id')
        if shipment_id:
            selected_shipment = Shipment.query.get(shipment_id)
        
        current_app.logger.debug("Rendering template print_form_template.html")
        return render_template('shipments/print_form_template.html', 
                             shipments=shipments,
                             selected_shipment=selected_shipment,
                             now=datetime.now)
    except Exception as e:
        current_app.logger.error(f"Error loading print form template: {str(e)}")
        current_app.logger.error("Stack trace:", exc_info=True)
        flash('Error loading print form template', 'error')
        return redirect(url_for('main.dashboard'))

@bp.route('/reports')
@login_required
def reports():
    logger.debug('Accessing reports page')
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
        
        # Get shipment statistics
        shipment_stats = db.session.query(
            func.count(Shipment.id).label('total_shipments'),
            func.sum(Shipment.total).label('total_revenue'),
            func.avg(Shipment.total).label('average_revenue'),
            func.sum(Shipment.vat).label('total_vat'),
            func.count(case((Shipment.status == 'delivered', 1))).label('delivered_shipments'),
            func.count(case((Shipment.status == 'cancelled', 1))).label('cancelled_shipments')
        ).filter(
            Shipment.created_at.between(start_date, end_date + timedelta(days=1))
        ).first()
        
        # Get daily revenue
        daily_revenue = db.session.query(
            func.date(Shipment.created_at).label('date'),
            func.sum(Shipment.total).label('revenue')
        ).filter(
            Shipment.created_at.between(start_date, end_date + timedelta(days=1))
        ).group_by(
            func.date(Shipment.created_at)
        ).all()
        
        # Format daily revenue for chart
        dates = [(start_date + timedelta(days=x)).strftime('%Y-%m-%d')
                for x in range((end_date - start_date).days + 1)]
        revenues = {date: 0 for date in dates}
        for date, revenue in daily_revenue:
            revenues[date.strftime('%Y-%m-%d')] = float(revenue)
        
        revenue_chart = {
            'labels': dates,
            'data': [revenues[date] for date in dates]
        }
        
        # Get customer group distribution
        customer_stats = db.session.query(
            Shipment.customer_group,
            func.count(Shipment.id).label('shipment_count'),
            func.sum(Shipment.total).label('total_revenue')
        ).filter(
            Shipment.created_at.between(start_date, end_date + timedelta(days=1))
        ).group_by(
            Shipment.customer_group
        ).all()
        
        return render_template('reports.html',
                             start_date=start_date,
                             end_date=end_date,
                             shipment_stats=shipment_stats,
                             revenue_chart=revenue_chart,
                             customer_stats=customer_stats)
    except Exception as e:
        logger.error(f'Error generating reports: {str(e)}')
        return render_template('reports.html', error=True)

@bp.route('/uploads/<path:file_id>')
def serve_image(file_id):
    """Serve uploaded images"""
    logger.debug(f'Attempting to serve image with file_id: {file_id}')
    try:
        # Initialize Appwrite storage
        storage = init_appwrite()
        logger.debug('Initialized Appwrite storage')
        
        try:
            bucket_id = current_app.config['APPWRITE_BUCKET_ID']
            logger.debug(f'Getting file from Appwrite - bucket: {bucket_id}, file: {file_id}')
            
            # First get the file details to determine content type
            file_details = storage.get_file(
                bucket_id=bucket_id,
                file_id=file_id
            )
            logger.debug(f'Got file details from Appwrite: {file_details["mimeType"]}')
            
            # Get the actual file data
            file_response = storage.get_file_download(
                bucket_id=bucket_id,
                file_id=file_id
            )
            logger.debug('Successfully retrieved file data from Appwrite')
            
            # Create response with proper mime type
            response = current_app.response_class(
                file_response,
                mimetype=file_details['mimeType']
            )
            
            # Add caching headers
            response.headers['Cache-Control'] = 'public, max-age=3600'
            
            logger.debug(f'Sending file response with mime type: {file_details["mimeType"]}')
            return response
            
        except Exception as e:
            logger.error(f'Error getting file from Appwrite: {str(e)}', exc_info=True)
            return 'File not found', 404
            
    except Exception as e:
        logger.error(f'Error serving image: {str(e)}', exc_info=True)
        return 'Error serving image', 500