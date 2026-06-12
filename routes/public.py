from flask import Blueprint, render_template, current_app

public_routes = Blueprint('public', __name__)

@public_routes.route('/')
def public_dashboard():
    mongo = current_app.mongo
    data = mongo.db.visitor_logs.find()
    return render_template('public_dashboard.html', data=data)
