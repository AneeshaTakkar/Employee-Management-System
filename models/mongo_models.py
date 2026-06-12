from flask_pymongo import PyMongo
from datetime import datetime
import numpy as np
import os
from flask import current_app

mongo = PyMongo()

def init_mongo(app):
    """Initialize MongoDB with Flask app"""
    mongo.init_app(app)
    
def get_mongo():
    """Get MongoDB instance from current app context"""
    if hasattr(current_app, 'mongo'):
        return current_app.mongo
    return mongo

def insert_employee(data):
    """Insert employee data into users collection"""
    db = get_mongo()
    return db.db.users.insert_one(data)

def get_employee_by_email(email):
    """Get employee by email from users collection"""
    db = get_mongo()
    return db.db.users.find_one({"email": email})

def get_all_employees():
    """Get all employees from users collection"""
    db = get_mongo()
    return list(db.db.users.find({'role': 'employee'}))
    
def get_employee_by_id(employee_id):
    """Get employee by ID from users collection"""
    from bson.objectid import ObjectId
    db = get_mongo()
    return db.db.users.find_one({'_id': ObjectId(employee_id)})

def insert_attendance(email, status):
    """Insert attendance record"""
    record = {
        "email": email,
        "status": status,
        "timestamp": datetime.now(),
        "date": datetime.now().strftime('%Y-%m-%d')
    }
    db = get_mongo()
    return db.db.attendance.insert_one(record)

def get_attendance(email):
    """Get attendance records for employee"""
    db = get_mongo()
    return list(db.db.attendance.find({"email": email}).sort('timestamp', -1))
    
def save_face_encoding(employee_id, encoding):
    """Save face encoding for employee"""
    from bson.objectid import ObjectId
    db = get_mongo()
    # Convert numpy array to list for MongoDB storage
    encoding_list = encoding.tolist() if hasattr(encoding, 'tolist') else encoding
    return db.db.face_encodings.update_one(
        {'employee_id': ObjectId(employee_id)},
        {'$set': {'encoding': encoding_list, 'updated_at': datetime.now()}},
        upsert=True
    )

def get_all_face_encodings():
    """Get all face encodings"""
    db = get_mongo()
    return list(db.db.face_encodings.find())
    
def save_camera_attendance(employee_id, status='Present'):
    """Save camera-based attendance"""
    from bson.objectid import ObjectId
    db = get_mongo()
    # Get employee email for consistency
    employee = get_employee_by_id(employee_id)
    if employee:
        record = {
            'employee_id': ObjectId(employee_id),
            'email': employee['email'],
            'date': datetime.now().strftime('%Y-%m-%d'),
            'timestamp': datetime.now(),
            'status': status,
            'method': 'Camera'
        }
        db.db.attendance.insert_one(record)
        return True
    return False

def apply_leave(email, reason, from_date, to_date, leave_type='Other', emergency=False):
    """Apply for leave"""
    db = get_mongo()
    return db.db.leaves.insert_one({
        "email": email,
        "reason": reason,
        "from_date": from_date,
        "to_date": to_date,
        "leave_type": leave_type,
        "emergency": emergency,
        "status": "Pending",
        "applied_at": datetime.now()
    })

def get_all_leave_applications():
    """Get all leave applications"""
    db = get_mongo()
    return list(db.db.leaves.find().sort('applied_at', -1))

def get_leave_applications_by_email(email):
    """Get leave applications for specific employee"""
    db = get_mongo()
    return list(db.db.leaves.find({"email": email}).sort('applied_at', -1))

def update_leave_status(application_id, status):
    """Update leave application status"""
    from bson.objectid import ObjectId
    db = get_mongo()
    return db.db.leaves.update_one(
        {"_id": ObjectId(application_id)},
        {"$set": {"status": status, "updated_at": datetime.now()}}
    )
    
def get_hr_faq():
    """Get all HR FAQ entries"""
    db = get_mongo()
    return list(db.db.hr_faq.find().sort('created_at', -1))
    
def save_hr_faq(question, answer):
    """Save HR FAQ entry"""
    db = get_mongo()
    return db.db.hr_faq.insert_one({
        'question': question,
        'answer': answer,
        'created_at': datetime.now()
    })
    
def get_employee_data_for_attrition():
    """Get employee data for attrition analysis"""
    db = get_mongo()
    pipeline = [
        {'$match': {'role': 'employee'}},
        {'$lookup': {
            'from': 'attendance',
            'localField': 'email',
            'foreignField': 'email',
            'as': 'attendance_records'
        }},
        {'$lookup': {
            'from': 'leaves',
            'localField': 'email',
            'foreignField': 'email',
            'as': 'leave_records'
        }}
    ]
    return list(db.db.users.aggregate(pipeline))

def get_user_by_email(email):
    """Get user by email (for authentication)"""
    db = get_mongo()
    return db.db.users.find_one({"email": email})

def create_user(name, email, password, role):
    """Create new user"""
    db = get_mongo()
    user_data = {
        'name': name,
        'email': email,
        'password': password,
        'role': role,
        'created_at': datetime.now(),
        'active': True,
        'department': 'General'  # Default department
    }
    return db.db.users.insert_one(user_data)

def update_user_profile(email, updates):
    db = get_mongo()
    return db.db.users.update_one({"email": email}, {"$set": updates})
