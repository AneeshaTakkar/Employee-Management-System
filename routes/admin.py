from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from utils.decorators import login_required
from models.mongo_models import get_all_employees, get_all_leave_applications, update_leave_status, get_employee_data_for_attrition
from datetime import datetime
from bson.objectid import ObjectId

# Blueprint
admin_routes = Blueprint('admin', __name__)

# -------------------------------
# Admin Dashboard Route
# -------------------------------
@admin_routes.route('/dashboard')
@login_required('admin')
def dashboard():
    try:
        employees = get_all_employees()
        leave_applications = get_all_leave_applications()
        from models.mongo_models import get_mongo
        db = get_mongo()
        total_attendance = db.db.attendance.count_documents({})
        
        # Calculate statistics
        total_employees = len(employees)
        total_leaves = len(leave_applications)
        pending_leaves = len([l for l in leave_applications if l.get('status') == 'Pending'])
        
        return render_template(
            'admin/dashboard.html',
            total_employees=total_employees,
            total_leaves=total_leaves,
            pending_leaves=pending_leaves,
            total_attendance=total_attendance,
            all_leaves=leave_applications[:10],  # Show recent 10
            employees=employees[:10]  # Show recent 10
        )
    except Exception as e:
        flash(f'Error loading admin dashboard: {str(e)}', 'danger')
        return render_template('admin/dashboard.html', 
                             total_employees=0, total_leaves=0, pending_leaves=0, total_attendance=0,
                             all_leaves=[], employees=[])

@admin_routes.route('/employees')
@login_required('admin')
def manage_employees():
    """Manage employees page"""
    try:
        employees = get_all_employees()
        return render_template('admin/manage_employees.html', employees=employees)
    except Exception as e:
        flash(f'Error loading employees: {str(e)}', 'danger')
        return render_template('admin/employees.html', employees=[])

@admin_routes.route('/leaves')
@login_required('admin')
def manage_leaves():
    """Manage leave applications"""
    try:
        leave_applications = get_all_leave_applications()
        return render_template('admin/manage_leaves.html', leaves=leave_applications)
    except Exception as e:
        flash(f'Error loading leave applications: {str(e)}', 'danger')
        return render_template('admin/manage_leaves.html', leaves=[])

@admin_routes.route('/approve_leave/<leave_id>')
@login_required('admin')
def approve_leave(leave_id):
    """Approve a leave application"""
    try:
        update_leave_status(leave_id, 'Approved')
        flash('Leave application approved successfully', 'success')
    except Exception as e:
        flash(f'Error approving leave: {str(e)}', 'danger')
    return redirect(url_for('admin.manage_leaves'))

@admin_routes.route('/reject_leave/<leave_id>')
@login_required('admin')
def reject_leave(leave_id):
    """Reject a leave application"""
    try:
        update_leave_status(leave_id, 'Rejected')
        flash('Leave application rejected', 'info')
    except Exception as e:
        flash(f'Error rejecting leave: {str(e)}', 'danger')
    return redirect(url_for('admin.manage_leaves'))

@admin_routes.route('/analytics')
@login_required('admin')
def analytics():
    """Analytics and reports page"""
    try:
        employee_data = get_employee_data_for_attrition()
        return render_template('admin/analytics.html', employee_data=employee_data)
    except Exception as e:
        flash(f'Error loading analytics: {str(e)}', 'danger')
        return render_template('admin/analytics.html', employee_data=[])

@admin_routes.route('/attendance')
@login_required('admin')
def manage_attendance():
    """Manage attendance records"""
    try:
        from models.mongo_models import get_mongo
        db = get_mongo()
        all_attendance = list(db.db.attendance.find().sort('timestamp', -1))
        return render_template('admin/manage_attendance.html', attendance=all_attendance)
    except Exception as e:
        flash(f'Error loading attendance records: {str(e)}', 'danger')
        return render_template('admin/manage_attendance.html', attendance=[])
