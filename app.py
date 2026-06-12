from flask import Flask, render_template
from flask_pymongo import PyMongo
from flask_session import Session
from bson.objectid import ObjectId
import os
from datetime import datetime

# Initialize Flask app
app = Flask(__name__)

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Configuration
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', '5f6b14f3c6a74e9a8d2e814f71fbbc90')
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SESSION_COOKIE_NAME'] = 'session'
app.config['MONGO_URI'] = os.environ.get('MONGO_URI', 'mongodb://localhost:27017/ems_pro')
app.config['SESSION_PERMANENT'] = False

# Initialize extensions
Session(app)
mongo = PyMongo(app)

# Test MongoDB connection
try:
    mongo.db.command('ping')
    print("✅ MongoDB connected successfully!")
    print(f"Database: {mongo.db.name}")
except Exception as e:
    print(f"❌ MongoDB connection failed: {e}")

# Make MongoDB available globally
app.mongo = mongo

# Initialize models with app context
from models.mongo_models import init_mongo
init_mongo(app)

# Import routes after app initialization
from routes.auth import auth_routes
from routes.admin import admin_routes
from routes.employee import employee_routes
from routes.public import public_routes
from routes.ai_features import ai_routes

# Register Blueprints
app.register_blueprint(auth_routes)
app.register_blueprint(admin_routes, url_prefix='/admin')
app.register_blueprint(employee_routes, url_prefix='/employee')
app.register_blueprint(public_routes, url_prefix='/public')
app.register_blueprint(ai_routes, url_prefix='/ai')

@app.route('/')
def index():
    from flask import render_template
    from datetime import datetime
    return render_template('index.html', now=datetime.now())

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
