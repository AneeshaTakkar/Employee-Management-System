from flask import Blueprint, render_template, session, redirect, url_for, request, flash
from models.mongo_models import get_user_by_email, get_leave_applications_by_email, get_attendance, apply_leave, insert_attendance
from utils.decorators import login_required
from datetime import datetime

employee_routes = Blueprint('employee', __name__)

@employee_routes.route('/dashboard')
@login_required('employee')
def dashboard():
    email = session.get('user')
    try:
        user = get_user_by_email(email)
        leaves = get_leave_applications_by_email(email)
        attendance = get_attendance(email)
        
        # Get recent attendance (last 10 records)
        recent_attendance = attendance[:10] if attendance else []
        
        return render_template('employee/dashboard.html', 
                             employee=user, 
                             leaves=leaves, 
                             attendance=recent_attendance,
                             total_leaves=len(leaves),
                             total_attendance=len(attendance))
    except Exception as e:
        flash(f'Error loading dashboard: {str(e)}', 'danger')
        return redirect(url_for('auth.login'))

@employee_routes.route('/apply_leave', methods=['GET', 'POST'])
@login_required('employee')
def apply_leave_route():
    if request.method == 'POST':
        from_date = request.form.get('from_date')
        to_date = request.form.get('to_date')
        reason = request.form.get('reason')
        leave_type = request.form.get('leave_type', 'Other')
        emergency = 'emergency' in request.form
        email = session.get('user')

        # Validate that all fields are filled
        if not from_date or not to_date or not reason:
            flash("All fields are required.", "danger")
            return redirect(url_for('employee.apply_leave_route'))

        try:
            # Apply for leave using the model function
            apply_leave(email, reason, from_date, to_date, leave_type, emergency)
            flash('Leave application submitted successfully.', 'success')
            return redirect(url_for('employee.dashboard'))
        except Exception as e:
            flash(f'Error submitting leave application: {str(e)}', 'danger')
            return redirect(url_for('employee.apply_leave_route'))
        return redirect(url_for('employee.dashboard'))
    
    return render_template('employee/leave.html')

@employee_routes.route('/mark_attendance')
@login_required('employee')
def mark_attendance():
    email = session.get('user')
    today = datetime.now().strftime("%Y-%m-%d")
    
    # Force debug info into flash messages so you can see it
    flash(f"DEBUG: Email={email}, Date={today}", 'warning')
    
    try:
        # Check if attendance already marked today
        from models.mongo_models import get_mongo
        db = get_mongo()
        already = db.db.attendance.find_one({'email': email, 'date': today})
        
        # Show what was found
        flash(f"DEBUG: Found existing record: {already is not None}", 'warning')
        
        if not already:
            result = insert_attendance(email, 'Present')
            flash('Attendance marked successfully!', 'success')
        else:
            # Show details of the existing record
            flash(f"Attendance already marked for today. Record: {already.get('timestamp', 'No timestamp') if already else 'None'}", 'info')
    except Exception as e:
        flash(f'Error marking attendance: {str(e)}', 'danger')
    
    return redirect(url_for('employee.dashboard'))

# Test route to verify debugging
@employee_routes.route('/test_attendance')
@login_required('employee')
def test_attendance():
    print("🔥 TEST: This route was called!")
    flash('Test route working!', 'info')
    return redirect(url_for('employee.dashboard'))

# ✅ NEW: View Profile Route
@employee_routes.route('/profile')
@login_required('employee')
def employee_profile():
    email = session.get('user')
    try:
        user = get_user_by_email(email)
        return render_template('employee/profile.html', user=user)
    except Exception as e:
        flash(f'Error loading profile: {str(e)}', 'danger')
        return redirect(url_for('employee.dashboard'))

@employee_routes.route('/profile/edit', methods=['POST'])
@login_required('employee')
def edit_profile():
    email = session.get('user')
    name = request.form.get('name')
    department = request.form.get('department')
    position = request.form.get('position')
    updates = {}
    if name:
        updates['name'] = name
    if department:
        updates['department'] = department
    if position:
        updates['position'] = position
    try:
        from models.mongo_models import update_user_profile
        update_user_profile(email, updates)
        flash('Profile updated successfully.', 'success')
    except Exception as e:
        flash(f'Error updating profile: {str(e)}', 'danger')
    return redirect(url_for('employee.employee_profile'))
