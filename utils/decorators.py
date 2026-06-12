from functools import wraps
from flask import session, redirect, url_for, flash

def login_required(role=None):
    def wrapper(fn):
        @wraps(fn)
        def decorated_view(*args, **kwargs):
            if 'user' not in session:
                flash("Please log in first.", "warning")
                return redirect(url_for('auth.login'))
            if role and session.get('role') != role:
                flash("Unauthorized access.", "danger")
                return redirect(url_for(f"{session.get('role')}.dashboard"))
            return fn(*args, **kwargs)
        return decorated_view
    return wrapper
