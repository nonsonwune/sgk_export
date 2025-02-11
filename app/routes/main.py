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
from app.models import ExportRequest

logger = logging.getLogger(__name__)

bp = Blueprint('main', __name__)

def get_critical_css():
    css_path = os.path.join(os.path.dirname(__file__), '../static/css/critical.css')
    with open(css_path, 'r') as f:
        return f'<style>{f.read()}</style>'

@bp.route('/')
def index():
    critical_css = get_critical_css()
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    return redirect(url_for('auth.login'))

@bp.route('/dashboard')
def dashboard():
    """Dashboard route with improved error handling and data validation."""
    try:
        current_app.logger.debug("=== Starting Dashboard Data Generation ===")
        
        # Get date ranges
        today = datetime.now()
        start_of_month = today.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        start_of_prev_month = (start_of_month - timedelta(days=1)).replace(day=1)
        
        current_app.logger.debug(f"Date ranges - Current month: {start_of_month}, Previous month: {start_of_prev_month}")
        
        # Get current month stats
        current_month_stats = get_monthly_stats(start_of_month, today)
        current_month_validated = validate_monthly_stats(current_month_stats)
        
        # Get previous month stats
        prev_month_stats = get_monthly_stats(start_of_prev_month, start_of_month)
        prev_month_validated = validate_monthly_stats(prev_month_stats)
        
        # Calculate percentage changes
        monthly_stats = {
            'total_shipments': current_month_validated['total_shipments'],
            'total_revenue': current_month_validated['total_revenue'],
            'active_shipments': current_month_validated['active_shipments'],
            'delivered_shipments': current_month_validated['delivered_shipments'],
            'shipment_change': calculate_percentage_change(
                current_month_validated['total_shipments'],
                prev_month_validated['total_shipments']
            ),
            'revenue_change': calculate_percentage_change(
                current_month_validated['total_revenue'],
                prev_month_validated['total_revenue']
            )
        }
        
        current_app.logger.debug(f"Final monthly stats: {monthly_stats}")
        
        # Get trend data with validation
        try:
            trend_data = get_monthly_trend_data()
            if not trend_data or not all(k in trend_data for k in ['labels', 'shipments', 'revenue']):
                current_app.logger.error("Invalid trend data structure")
                trend_data = {
                    'labels': [],
                    'shipments': [],
                    'revenue': []
                }
        except Exception as e:
            current_app.logger.error(f"Error getting trend data: {str(e)}", exc_info=True)
            trend_data = {
                'labels': [],
                'shipments': [],
                'revenue': []
            }
            
        # Get recent shipments
        try:
            recent_shipments = ExportRequest.query.order_by(
                ExportRequest.created_at.desc()
            ).limit(5).all()
            current_app.logger.debug(f"Retrieved {len(recent_shipments)} recent shipments")
        except Exception as e:
            current_app.logger.error(f"Error getting recent shipments: {str(e)}", exc_info=True)
            recent_shipments = []
        
        # Prepare template data
        template_data = {
            'monthly_stats': monthly_stats,
            'trend_data': trend_data,
            'recent_shipments': recent_shipments,
            'error': False
        }
        
        # Log template data for debugging
        current_app.logger.debug("=== Template Data Debug ===")
        current_app.logger.debug(f"Template data type: {type(template_data)}")
        current_app.logger.debug(f"Monthly stats: {monthly_stats}")
        current_app.logger.debug(f"Trend data type: {type(trend_data)}")
        current_app.logger.debug(f"Trend data: {trend_data}")
        current_app.logger.debug(f"Recent shipments count: {len(recent_shipments)}")
        
        # Ensure trend_data is not None
        if trend_data is None:
            current_app.logger.warning("Trend data is None, initializing empty structure")
            trend_data = {
                'labels': [],
                'shipments': [],
                'revenue': []
            }
            template_data['trend_data'] = trend_data
        
        return render_template('dashboard.html', **template_data)
        
    except Exception as e:
        current_app.logger.error(f"Error in dashboard route: {str(e)}", exc_info=True)
        return render_template('dashboard.html', error=True)

def get_monthly_stats(start_date, end_date):
    """Get monthly statistics with proper error handling."""
    try:
        current_app.logger.debug(f"Fetching monthly stats from {start_date} to {end_date}")
        stats = db.session.query(
            func.count(ExportRequest.id).label('total_shipments'),
            func.sum(ExportRequest.total).label('total_revenue'),
            func.count(case((ExportRequest.status == 'Active', 1))).label('active_shipments'),
            func.count(case((ExportRequest.status == 'Delivered', 1))).label('delivered_shipments')
        ).filter(
            ExportRequest.created_at.between(start_date, end_date)
        ).first()
        
        current_app.logger.debug(f"Monthly stats query result: {stats}")
        return stats
        
    except Exception as e:
        current_app.logger.error(f"Error getting monthly stats: {str(e)}", exc_info=True)
        return None

def validate_monthly_stats(stats):
    """Validate and clean monthly statistics."""
    default_stats = {
        'total_shipments': 0,
        'total_revenue': 0.0,
        'active_shipments': 0,
        'delivered_shipments': 0
    }
    
    if not stats:
        current_app.logger.warning("Monthly stats is None, returning defaults")
        return default_stats
        
    try:
        validated = {
            'total_shipments': int(getattr(stats, 'total_shipments', 0) or 0),
            'total_revenue': float(getattr(stats, 'total_revenue', 0) or 0),
            'active_shipments': int(getattr(stats, 'active_shipments', 0) or 0),
            'delivered_shipments': int(getattr(stats, 'delivered_shipments', 0) or 0)
        }
        current_app.logger.debug(f"Validated monthly stats: {validated}")
        return validated
        
    except Exception as e:
        current_app.logger.error(f"Error validating monthly stats: {str(e)}", exc_info=True)
        return default_stats

def calculate_percentage_change(current, previous):
    """Calculate percentage change with proper validation."""
    try:
        if not isinstance(current, (int, float)) or not isinstance(previous, (int, float)):
            current_app.logger.warning(f"Invalid types for percentage change - current: {type(current)}, previous: {type(previous)}")
            return 0
        
        if previous == 0:
            return 100 if current > 0 else 0
            
        change = ((current - previous) / previous) * 100
        current_app.logger.debug(f"Calculated percentage change: {change}% (current: {current}, previous: {previous})")
        return change
        
    except Exception as e:
        current_app.logger.error(f"Error calculating percentage change: {str(e)}", exc_info=True)
        return 0

def get_monthly_trend_data():
    """Get monthly trend data with comprehensive logging."""
    try:
        # Get the last 6 months of data
        end_date = datetime.now()
        start_date = end_date - timedelta(days=180)
        
        current_app.logger.debug(f"=== Starting Trend Data Generation ===")
        current_app.logger.debug(f"Date range: {start_date} to {end_date}")
        
        try:
            # Query the data
            monthly_data = db.session.query(
                func.date_trunc('month', ExportRequest.created_at).label('month'),
                func.count(ExportRequest.id).label('shipment_count'),
                func.sum(ExportRequest.total).label('revenue')
            ).filter(
                ExportRequest.created_at >= start_date
            ).group_by(
                func.date_trunc('month', ExportRequest.created_at)
            ).order_by(
                func.date_trunc('month', ExportRequest.created_at)
            ).all()
            
            current_app.logger.debug(f"Query successful - Found {len(monthly_data)} months of data")
            if monthly_data:
                current_app.logger.debug(f"Sample month data: {monthly_data[0]}")
                current_app.logger.debug(f"Data types - month: {type(monthly_data[0].month)}, count: {type(monthly_data[0].shipment_count)}, revenue: {type(monthly_data[0].revenue)}")
            
        except Exception as db_error:
            current_app.logger.error(f"Database query error: {str(db_error)}", exc_info=True)
            raise ValueError(f"Failed to fetch monthly trend data: {str(db_error)}")
        
        # Generate all months in the range
        months = []
        current_date = end_date
        for _ in range(6):
            months.append(current_date.replace(day=1))
            current_date = current_date.replace(day=1) - timedelta(days=1)
        months.reverse()
        
        current_app.logger.debug(f"Generated month range: {[m.strftime('%Y-%m') for m in months]}")
        
        try:
            # Create a mapping of month to data
            data_map = {}
            for data in monthly_data:
                month_key = data.month.strftime('%Y-%m')
                data_map[month_key] = {
                    'count': data.shipment_count,
                    'revenue': float(data.revenue or 0)
                }
                current_app.logger.debug(f"Mapped data for {month_key}: {data_map[month_key]}")
            
        except Exception as mapping_error:
            current_app.logger.error(f"Error creating data map: {str(mapping_error)}", exc_info=True)
            raise ValueError(f"Failed to process monthly data: {str(mapping_error)}")
        
        try:
            # Fill in the result using all months
            result = {
                'labels': [d.strftime('%b') for d in months],
                'shipments': [],
                'revenue': []
            }
            
            # Fill data arrays
            for month in months:
                month_key = month.strftime('%Y-%m')
                month_data = data_map.get(month_key, {'count': 0, 'revenue': 0.0})
                result['shipments'].append(month_data['count'])
                result['revenue'].append(month_data['revenue'])
                
                current_app.logger.debug(f"Month {month_key}: shipments={month_data['count']}, revenue={month_data['revenue']}")
            
            # Validate result structure
            current_app.logger.debug("=== Validating Result Structure ===")
            current_app.logger.debug(f"Labels length: {len(result['labels'])}")
            current_app.logger.debug(f"Shipments length: {len(result['shipments'])}")
            current_app.logger.debug(f"Revenue length: {len(result['revenue'])}")
            current_app.logger.debug(f"Sample data - First month: {result['labels'][0]}, shipments: {result['shipments'][0]}, revenue: {result['revenue'][0]}")
            
            return result
            
        except Exception as result_error:
            current_app.logger.error(f"Error creating result structure: {str(result_error)}", exc_info=True)
            raise ValueError(f"Failed to structure trend data: {str(result_error)}")
        
    except Exception as e:
        current_app.logger.error(f"=== Trend Data Generation Failed ===")
        current_app.logger.error(f"Error type: {type(e)}")
        current_app.logger.error(f"Error message: {str(e)}")
        current_app.logger.error("Stack trace:", exc_info=True)
        
        # Return empty data structure on error
        return {
            'labels': [],
            'shipments': [],
            'revenue': []
        }

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