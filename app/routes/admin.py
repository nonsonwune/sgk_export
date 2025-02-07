from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from ..models.user import User
from ..extensions import db

bp = Blueprint('admin', __name__, url_prefix='/admin')

@bp.route('/users')
@login_required
def manage_users():
    if not current_user.is_admin:
        flash('Access denied', 'danger')
        return redirect(url_for('shipments.new_shipment'))
    
    users = User.query.all()
    return render_template('manage_users.html', users=users)

@bp.route('/create-user', methods=['GET', 'POST'])
@login_required
def create_user():
    if not current_user.is_admin:
        flash('Access denied', 'danger')
        return redirect(url_for('shipments.new_shipment'))
        
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        name = request.form.get('name')
        
        if User.query.filter_by(username=username).first():
            flash('Username already exists', 'danger')
        else:
            new_user = User(username=username, name=name)
            new_user.set_password(password)
            db.session.add(new_user)
            db.session.commit()
            flash('User created successfully', 'success')
            return redirect(url_for('admin.manage_users'))
            
    return render_template('create_user.html')

@bp.route('/reset-password/<int:user_id>', methods=['POST'])
@login_required
def reset_user_password(user_id):
    if not current_user.is_admin:
        flash('Access denied', 'error')
        return redirect(url_for('shipments.new_shipment'))
    
    user = User.query.get_or_404(user_id)
    
    if user.is_superuser and not current_user.is_superuser:
        flash('Access denied. Only Super Users can modify Super User accounts.', 'error')
        return redirect(url_for('admin.manage_users'))
    
    new_password = request.form.get('new_password')
    
    if len(new_password) < 8:
        flash('Password must be at least 8 characters long', 'error')
        return redirect(url_for('admin.manage_users'))
    
    user.set_password(new_password)
    db.session.commit()
    flash(f'Password reset for user {user.username}', 'success')
    return redirect(url_for('admin.manage_users'))

@bp.route('/delete-user/<int:user_id>', methods=['POST'])
@login_required
def delete_user(user_id):
    if not current_user.is_admin:
        flash('Access denied', 'error')
        return redirect(url_for('shipments.new_shipment'))
    
    user = User.query.get_or_404(user_id)
    
    if user.is_superuser and not current_user.is_superuser:
        flash('Access denied. Only Super Users can delete Super User accounts.', 'error')
        return redirect(url_for('admin.manage_users'))
    
    if user.is_admin and User.query.filter_by(is_admin=True).count() <= 1:
        flash('Cannot delete the last administrator', 'error')
        return redirect(url_for('admin.manage_users'))
    
    if user.id == current_user.id:
        flash('Cannot delete your own account', 'error')
        return redirect(url_for('admin.manage_users'))
    
    username = user.username
    db.session.delete(user)
    db.session.commit()
    flash(f'User {username} has been deleted', 'success')
    return redirect(url_for('admin.manage_users'))

@bp.route('/manage-admins')
@login_required
def manage_admins():
    if not current_user.is_superuser:
        flash('Access denied. Superuser privileges required.', 'error')
        return redirect(url_for('main.dashboard'))
    
    users = User.query.all()
    return render_template('manage_admins.html', users=users)

@bp.route('/add-admin', methods=['POST'])
@login_required
def add_admin():
    if not current_user.is_superuser:
        flash('Access denied. Superuser privileges required.', 'error')
        return redirect(url_for('main.dashboard'))
    
    try:
        username = request.form.get('username')
        name = request.form.get('name')
        password = request.form.get('password')
        
        if not all([username, name, password]):
            flash('All fields are required.', 'error')
            return redirect(url_for('admin.manage_admins'))
        
        if User.query.filter_by(username=username).first():
            flash('Username already exists.', 'error')
            return redirect(url_for('admin.manage_admins'))
        
        new_admin = User(
            username=username,
            name=name,
            is_admin=True,
            is_superuser=False
        )
        new_admin.set_password(password)
        
        db.session.add(new_admin)
        db.session.commit()
        
        flash('Administrator added successfully.', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash('Error adding administrator.', 'error')
    
    return redirect(url_for('admin.manage_admins'))

@bp.route('/modify-admin/<int:user_id>', methods=['POST'])
@login_required
def modify_admin(user_id):
    if not current_user.is_superuser:
        flash('Access denied. Superuser privileges required.', 'error')
        return redirect(url_for('main.dashboard'))
    
    try:
        user = User.query.get_or_404(user_id)
        
        if user.is_superuser:
            flash('Cannot modify superuser accounts.', 'error')
            return redirect(url_for('admin.manage_admins'))
        
        username = request.form.get('username')
        name = request.form.get('name')
        password = request.form.get('password')
        
        if not all([username, name]):
            flash('Username and name are required.', 'error')
            return redirect(url_for('admin.manage_admins'))
        
        existing_user = User.query.filter_by(username=username).first()
        if existing_user and existing_user.id != user_id:
            flash('Username already exists.', 'error')
            return redirect(url_for('admin.manage_admins'))
        
        user.username = username
        user.name = name
        if password:
            user.set_password(password)
        
        db.session.commit()
        flash('Administrator updated successfully.', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash('Error updating administrator.', 'error')
    
    return redirect(url_for('admin.manage_admins'))

@bp.route('/delete-admin/<int:user_id>', methods=['POST'])
@login_required
def delete_admin(user_id):
    if not current_user.is_superuser:
        flash('Access denied. Superuser privileges required.', 'error')
        return redirect(url_for('main.dashboard'))
    
    try:
        user = User.query.get_or_404(user_id)
        
        if user.is_superuser:
            flash('Cannot delete superuser accounts.', 'error')
            return redirect(url_for('admin.manage_admins'))
        
        if user.id == current_user.id:
            flash('Cannot delete your own account.', 'error')
            return redirect(url_for('admin.manage_admins'))
        
        db.session.delete(user)
        db.session.commit()
        flash('Administrator deleted successfully.', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash('Error deleting administrator.', 'error')
    
    return redirect(url_for('admin.manage_admins')) 