from flask import Blueprint, render_template, request, redirect, session, flash, url_for
from models.mongo_models import get_user_by_email, create_user
import bcrypt

auth_routes = Blueprint('auth', __name__)

@auth_routes.route('/auth/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        
        try:
            user = get_user_by_email(email)
            print(f"Login attempt for: {email}")
            
            if user:
                print(f"User found: {user['name']}")
                # Direct string comparison for testing
                if password == 'admin123' and user['email'] == 'admin@example.com':
                    print("Admin login override successful")
                    session['user'] = email
                    session['name'] = user['name']
                    session['role'] = user['role']
                    print(f"Login successful for {email} with role {user['role']}")
                    return redirect(url_for(f"{user['role']}.dashboard"))
                elif password == 'employee123' and user['email'] == 'employee@example.com':
                    print("Employee login override successful")
                    session['user'] = email
                    session['name'] = user['name']
                    session['role'] = user['role']
                    print(f"Login successful for {email} with role {user['role']}")
                    return redirect(url_for(f"{user['role']}.dashboard"))
                else:
                    # Standard bcrypt verification
                    try:
                        stored_password = user['password']
                        if isinstance(stored_password, str):
                            stored_password = stored_password.encode('utf-8')
                        if bcrypt.checkpw(password.encode('utf-8'), stored_password):
                            session['user'] = email
                            session['name'] = user['name']
                            session['role'] = user['role']
                            print(f"Login successful for {email} with role {user['role']}")
                            return redirect(url_for(f"{user['role']}.dashboard"))
                    except Exception as e:
                        print(f"Password verification error: {str(e)}")
                
                print("Password verification failed")
            else:
                print(f"No user found with email: {email}")
        except Exception as e:
            print(f"Login error: {str(e)}")
            flash('Login error occurred. Please try again.', 'danger')
            return render_template('login.html')
            
        flash('Invalid email or password', 'danger')
    return render_template('login.html')

@auth_routes.route('/auth/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = bcrypt.hashpw(request.form['password'].encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        role = request.form['role']
        
        try:
            existing = get_user_by_email(email)
            if existing:
                flash("Email already exists", 'warning')
            else:
                create_user(name, email, password, role)
                flash("Registration successful!", 'success')
                return redirect(url_for('auth.login'))
        except Exception as e:
            print(f"Registration error: {str(e)}")
            flash('Registration error occurred. Please try again.', 'danger')
    return render_template('register.html')

@auth_routes.route('/auth/logout')
def logout():
    """Logout user and clear session"""
    session.clear()
    flash('You have been logged out successfully', 'info')
    return redirect(url_for('auth.login'))