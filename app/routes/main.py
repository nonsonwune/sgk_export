from flask import Blueprint, render_template, redirect, url_for, request, flash, current_app, send_from_directory
from flask_login import login_required, current_user
from ..models.shipment import Shipment
from ..extensions import db
from sqlalchemy import func, case
import logging
from datetime import datetime, timedelta
import os
import mimetypes
from ..utils.file_storage import get_upload_path
from app.models import ExportRequest

logger = logging.getLogger(__name__)

bp = Blueprint('main', __name__)

def get_critical_css():
    css_path = os.path.join(os.path.dirname(__file__), '../static/css/critical.css')
    with open(css_path, 'r') as f:
        return f'<style>{f.read()}</style>'

@bp.route('/')
def index():
    """Root route with enhanced error tracking"""
    logger.debug("=== Starting Root Route Handler ===")
    try:
        logger.debug("=== Application State ===")
        logger.debug(f"Debug mode: {current_app.debug}")
        logger.debug(f"Testing mode: {current_app.testing}")
        logger.debug(f"Secret key set: {'SECRET_KEY' in current_app.config}")
        
        logger.debug("\n=== Database Configuration ===")
        logger.debug(f"Database URL configured: {'SQLALCHEMY_DATABASE_URI' in current_app.config}")
        logger.debug(f"Database connection options: {current_app.config.get('SQLALCHEMY_ENGINE_OPTIONS', {})}")
        
        logger.debug("\n=== Authentication State ===")
        logger.debug(f"Login manager configured: {hasattr(current_app, 'login_manager')}")
        logger.debug(f"Current user: {current_user}")
        logger.debug(f"User authenticated: {current_user.is_authenticated if hasattr(current_user, 'is_authenticated') else 'No auth attribute'}")
        
        if current_user.is_authenticated:
            logger.debug("\n=== Authenticated User Details ===")
            logger.debug(f"User ID: {current_user.id}")
            logger.debug(f"Username: {current_user.username}")
            logger.debug("Redirecting to dashboard")
            return redirect(url_for('main.dashboard'))
        
        logger.debug("User not authenticated, redirecting to login")
        return redirect(url_for('auth.login'))
    except Exception as e:
        logger.error("\n=== Error in Root Route ===")
        logger.error(f"Error type: {type(e).__name__}")
        logger.error(f"Error message: {str(e)}")
        logger.error("Stack trace:", exc_info=True)
        logger.error(f"Request details: {request.environ}")
        return render_template('error.html', error=f"An error occurred: {str(e)}"), 500

@bp.route('/terms')
def terms():
    """Terms and conditions page"""
    logger.debug("Accessing terms and conditions page")
    try:
        return render_template('terms.html')
    except Exception as e:
        logger.error(f"Error loading terms page: {str(e)}")
        return render_template('error.html', error=f"An error occurred: {str(e)}"), 500

@bp.route('/dashboard')
@login_required
def dashboard():
    try:
        current_app.logger.debug('=== Starting Dashboard Data Generation ===')
        
        # Calculate date ranges
        current_month_start = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        previous_month_start = (current_month_start - timedelta(days=1)).replace(day=1)
        
        current_app.logger.debug(f'Date ranges - Current month: {current_month_start}, Previous month: {previous_month_start}')
        
        # Get current month stats
        current_app.logger.debug(f'Fetching monthly stats from {current_month_start} to {datetime.now()}')
        current_stats = db.session.query(
            func.count(Shipment.id).label('total_shipments'),
            func.sum(Shipment.total).label('total_revenue'),
            func.count(case((Shipment.status.in_(['processing', 'in_transit']), 1))).label('active_shipments'),
            func.count(case((Shipment.status == 'delivered', 1))).label('delivered_shipments')
        ).filter(
            Shipment.created_at >= current_month_start
        ).first()
        
        current_app.logger.debug(f'Monthly stats query result: {current_stats}')
        
        # Format current month stats
        monthly_stats = {
            'total_shipments': current_stats.total_shipments or 0,
            'total_revenue': float(current_stats.total_revenue or 0),
            'active_shipments': current_stats.active_shipments or 0,
            'delivered_shipments': current_stats.delivered_shipments or 0
        }
        
        current_app.logger.debug(f'Validated monthly stats: {monthly_stats}')
        
        # Get previous month stats for comparison
        current_app.logger.debug(f'Fetching monthly stats from {previous_month_start} to {current_month_start}')
        previous_stats = db.session.query(
            func.count(Shipment.id).label('total_shipments'),
            func.sum(Shipment.total).label('total_revenue'),
            func.count(case((Shipment.status.in_(['processing', 'in_transit']), 1))).label('active_shipments'),
            func.count(case((Shipment.status == 'delivered', 1))).label('delivered_shipments')
        ).filter(
            Shipment.created_at.between(previous_month_start, current_month_start)
        ).first()
        
        current_app.logger.debug(f'Monthly stats query result: {previous_stats}')
        
        # Format previous month stats
        previous_month_stats = {
            'total_shipments': previous_stats.total_shipments or 0,
            'total_revenue': float(previous_stats.total_revenue or 0),
            'active_shipments': previous_stats.active_shipments or 0,
            'delivered_shipments': previous_stats.delivered_shipments or 0
        }
        
        current_app.logger.debug(f'Validated monthly stats: {previous_month_stats}')
        
        # Calculate changes
        monthly_stats['shipment_change'] = calculate_percentage_change(
            previous_month_stats['total_shipments'],
            monthly_stats['total_shipments']
        )
        monthly_stats['revenue_change'] = calculate_percentage_change(
            previous_month_stats['total_revenue'],
            monthly_stats['total_revenue']
        )
        
        current_app.logger.debug(f'Final monthly stats: {monthly_stats}')
        
        # Get status distribution
        status_counts = db.session.query(
            Shipment.status,
            func.count(Shipment.id).label('count')
        ).filter(
            Shipment.created_at >= current_month_start
        ).group_by(Shipment.status).all()
        
        # Format status counts with defaults
        monthly_stats.update({
            'pending_count': 0,
            'processing_count': 0,
            'in_transit_count': 0,
            'delivered_count': 0,
            'cancelled_count': 0
        })
        
        for status, count in status_counts:
            monthly_stats[f'{status}_count'] = count
        
        current_app.logger.debug(f'Status distribution: {status_counts}')
        
        # Get trend data
        current_app.logger.debug('=== Starting Trend Data Generation ===')
        end_date = datetime.now()
        start_date = end_date - timedelta(days=180)
        current_app.logger.debug(f'Date range: {start_date} to {end_date}')
        
        trend_data = db.session.query(
            func.date_trunc('month', Shipment.created_at).label('month'),
            func.count(Shipment.id).label('count'),
            func.sum(Shipment.total).label('revenue')
            ).filter(
            Shipment.created_at.between(start_date, end_date)
        ).group_by('month').order_by('month').all()
            
        current_app.logger.debug(f'Query successful - Found {len(trend_data)} months of data')
        
        trends = {
            'labels': [t.month.strftime('%Y-%m-%d') for t in trend_data],
            'shipments': [t.count for t in trend_data],
            'revenue': [float(t.revenue or 0) for t in trend_data]
        }
        
        current_app.logger.debug(f'Processed trend data: {trends}')
        
        # Get recent shipments
        recent_shipments = Shipment.query.order_by(
            Shipment.created_at.desc()
        ).limit(5).all()
        
        current_app.logger.debug(f'Retrieved {len(recent_shipments)} recent shipments')
        for shipment in recent_shipments:
            current_app.logger.debug(f'Shipment {shipment.waybill_number}: Status={shipment.status}, Created by={shipment.created_by}')
        
        # Debug template data
        current_app.logger.debug('=== Template Data Debug ===')
        template_data = {
            'monthly_stats': monthly_stats,
            'trends': trends,
            'recent_shipments': recent_shipments
        }
        current_app.logger.debug(f'Template data type: {type(template_data)}')
        current_app.logger.debug(f'Monthly stats: {monthly_stats}')
        current_app.logger.debug(f'Trend data type: {type(trends)}')
        current_app.logger.debug(f'Trend data: {trends}')
        current_app.logger.debug(f'Recent shipments count: {len(recent_shipments)}')
        
        return render_template('dashboard.html', **template_data)
            
    except Exception as e:
        current_app.logger.error(f'Error generating dashboard: {str(e)}', exc_info=True)
        return render_template('error.html', error='Failed to load dashboard data'), 500

def calculate_percentage_change(old_value, new_value):
    """Calculate percentage change between two values"""
    if old_value == 0:
        return 100 if new_value > 0 else 0
    return ((new_value - old_value) / old_value) * 100

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
    """Serve uploaded images from local storage"""
    logger.debug(f'Attempting to serve image with file_id: {file_id}')
    try:
        # Get upload folder path
        upload_path = get_upload_path()
        logger.debug(f'Upload path: {upload_path}')
        
        # Find the file with the given file_id (could have different extensions)
        for filename in os.listdir(upload_path):
            if filename.startswith(file_id):
                file_path = os.path.join(upload_path, filename)
                logger.debug(f'Found file: {file_path}')
                
                # Determine content type
                content_type, _ = mimetypes.guess_type(file_path)
                if not content_type:
                    content_type = 'application/octet-stream'
                
                logger.debug(f'Serving file with content type: {content_type}')
                
                # Return the file with proper mimetype
                return send_from_directory(
                    upload_path, 
                    filename,
                    mimetype=content_type,
                    as_attachment=False,
                    max_age=3600
                )
        
        logger.error(f'No file found with ID: {file_id}')
        return 'File not found', 404
                
    except Exception as e:
        logger.error(f'Error serving image: {str(e)}', exc_info=True)
        return 'Error serving image', 500

def calculate_avg_delivery_time(start_date, end_date):
    logger.debug(f"Calculating average delivery time between {start_date} and {end_date}")
    try:
        delivered_shipments = Shipment.query.filter(
            Shipment.status == 'delivered',
            Shipment.created_at.between(start_date, end_date)
        ).all()
        
        if not delivered_shipments:
            logger.debug("No delivered shipments found in date range")
            return 0.0
            
        total_days = 0
        valid_shipments = 0
        
        for shipment in delivered_shipments:
            if hasattr(shipment, 'delivery_date') and shipment.delivery_date:
                days = (shipment.delivery_date - shipment.created_at).days
                if days >= 0:  # Ensure valid delivery time
                    total_days += days
                    valid_shipments += 1
        
        avg_days = total_days / valid_shipments if valid_shipments > 0 else 0
        logger.debug(f"Calculated average delivery time: {avg_days:.1f} days")
        return avg_days
    except Exception as e:
        logger.error(f"Error calculating average delivery time: {str(e)}")
        return 0.0

def calculate_monthly_stats():
    logger.debug("=== Starting Monthly Stats Calculation ===")
    try:
        current_month_start = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        previous_month_start = (current_month_start - timedelta(days=1)).replace(day=1)
        
        # Get current month stats
        current_stats = get_period_stats(current_month_start, datetime.now())
        previous_stats = get_period_stats(previous_month_start, current_month_start)
        
        # Calculate changes
        shipment_change = calculate_percentage_change(
            previous_stats['total_shipments'],
            current_stats['total_shipments']
        )
        revenue_change = calculate_percentage_change(
            previous_stats['total_revenue'],
            current_stats['total_revenue']
        )
        
        # Add average delivery time
        current_stats['avg_delivery_time'] = calculate_avg_delivery_time(
            current_month_start,
            datetime.now()
        )
        
        # Combine all stats
        monthly_stats = {
            **current_stats,
            'shipment_change': shipment_change,
            'revenue_change': revenue_change
        }
        
        logger.debug(f"Final monthly stats: {monthly_stats}")
        return monthly_stats
        
    except Exception as e:
        logger.error(f"Error calculating monthly stats: {str(e)}")
        return {
            'total_shipments': 0,
            'total_revenue': 0.0,
            'active_shipments': 0,
            'delivered_shipments': 0,
            'avg_delivery_time': 0.0,
            'shipment_change': 0,
            'revenue_change': 0
        }