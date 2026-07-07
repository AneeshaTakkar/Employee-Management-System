from flask import Blueprint, render_template, request, redirect, url_for, session, flash, jsonify
from utils.decorators import login_required
from models.mongo_models import get_employee_by_email, get_employee_by_id
import os
import numpy as np
import cv2
import base64
from datetime import datetime
from PIL import Image
import io

# Blueprint
ai_routes = Blueprint('ai', __name__)

# Try to import AI models with fallbacks
try:
    from ai_models.face_recognition_utils import recognize_faces_from_camera, encode_face, generate_sample_encodings, recognize_faces_in_image
except ImportError as e:
    # Soft fallback: instead of hard-failing, defer to runtime import within utils and provide actionable message
    print(f"[WARNING] Could not import face recognition utils: {e}")
    def recognize_faces_from_camera():
        return False, "Face recognition is currently unavailable at runtime. Please ensure the server uses the correct virtual environment and that the 'deepface' package is installed."
    def encode_face(image_path, employee_id):
        return False, "Face encoding is currently unavailable at runtime. Please ensure the server uses the correct virtual environment and that the 'deepface' package is installed."
    def generate_sample_encodings():
        return False, "Sample encodings are currently unavailable at runtime. Please ensure the server uses the correct virtual environment and that the 'deepface' package is installed."
    def recognize_faces_in_image(_img):
        return False, "Face recognition is currently unavailable at runtime. Please ensure the server uses the correct virtual environment and that the 'deepface' package is installed.", {}

try:
    from ai_models.ml_models import predict_leave_approval, predict_attrition_risk, initialize_models
    initialize_models()
except ImportError:
    def predict_leave_approval(*args):
        return 0.5  # Default probability
    def predict_attrition_risk(*args):
        return 0.3  # Default risk
    def initialize_models():
        pass

try:
    from ai_models.hr_chatbot import get_chatbot_response
except ImportError:
    def get_chatbot_response(question):
        return "HR Chatbot is currently unavailable. Please contact HR directly."

# Initialize sample face encodings
@ai_routes.route('/initialize_face_samples', methods=['GET'])
@login_required('admin')
def initialize_face_samples():
    """Initialize sample face encodings for demo purposes"""
    try:
        success, message = generate_sample_encodings()
        if success:
            flash(message, 'success')
        else:
            flash(f"Error: {message}", 'danger')
    except Exception as e:
        flash(f"Error initializing face samples: {str(e)}", 'danger')
    
    return redirect(url_for('admin.dashboard'))

# Camera-based Attendance
@ai_routes.route('/camera_attendance', methods=['GET', 'POST'])
@login_required('employee')
def camera_attendance():
    """Camera-based attendance page"""
    if request.method == 'POST':
        if 'capture' in request.form:
            # Start face recognition process
            try:
                # Debug: verify which implementation is used and whether FR is available
                try:
                    from ai_models.face_recognition_utils import FACE_RECOGNITION_AVAILABLE as _FR_AVAIL
                    print(f"[DEBUG] FACE_RECOGNITION_AVAILABLE = {_FR_AVAIL}")
                except Exception as _e:
                    print(f"[DEBUG] Could not import FR flag: {_e}")
                print(f"[DEBUG] recognize_faces_from_camera from module: {recognize_faces_from_camera.__module__}")
                
                success, message = recognize_faces_from_camera()
                if success:
                    flash(message, 'success')
                else:
                    flash(f"Error: {message}", 'danger')
            except Exception as e:
                flash(f"Face recognition error: {str(e)}", 'danger')
            
            return redirect(url_for('ai.camera_attendance'))
        
        elif 'upload' in request.form and 'employee_id' in request.form:
            # Handle face image upload
            if 'face_image' not in request.files:
                flash('No file selected', 'danger')
                return redirect(request.url)
            
            file = request.files['face_image']
            if file.filename == '':
                flash('No file selected', 'danger')
                return redirect(request.url)
            
            if file:
                try:
                    # Save the uploaded image
                    employee_id = request.form['employee_id']
                    image_dir = os.path.join('static', 'images', 'employees')
                    os.makedirs(image_dir, exist_ok=True)
                    final_path = os.path.join(image_dir, f"{employee_id}.jpg")
                    try:
                        file.stream.seek(0)
                        data = file.read()
                        bio = io.BytesIO(data)
                        im = Image.open(bio)
                        im = im.convert('RGB')
                        im.save(final_path, format='JPEG')
                    except Exception:
                        flash('Unsupported image type. Please upload a valid image file.', 'danger')
                        return redirect(request.url)
                    
                    # Encode the face
                    success, message = encode_face(final_path, employee_id)
                    
                    if success:
                        flash(f"Face encoded successfully for employee ID: {employee_id}", 'success')
                    else:
                        flash(f"Error encoding face: {message}", 'danger')
                except Exception as e:
                    flash(f"Error processing image: {str(e)}", 'danger')
                
                return redirect(url_for('ai.camera_attendance'))
    
    # For GET request, render the template
    try:
        employees = []
        from models.mongo_models import get_all_employees
        employees = get_all_employees()
        fr_available = False
        try:
            from deepface import DeepFace
            fr_available = True
        except Exception:
            fr_available = False
        return render_template('ai/camera_attendance.html', employees=employees, fr_available=fr_available)
    except Exception as e:
        flash(f"Error loading page: {str(e)}", "danger")
        return render_template('ai/camera_attendance.html', employees=[], fr_available=False)

# Leave Approval Prediction
@ai_routes.route('/leave_prediction', methods=['GET', 'POST'])
@login_required('employee')
def leave_prediction():
    """Leave approval prediction page"""
    prediction = None
    probability = None
    
    if request.method == 'POST':
        try:
            # Get form data
            emergency = 1 if request.form.get('emergency') == 'on' else 0
            leave_duration = int(request.form.get('duration', 1))
            leaves_taken_last_month = int(request.form.get('leaves_taken', 0))
            performance_score = float(request.form.get('performance_score', 3.0))
            department = request.form.get('department', 'IT')
            
            # Get prediction
            probability = predict_leave_approval(
                emergency, leave_duration, leaves_taken_last_month, performance_score, department
            )
            
            # Determine prediction text
            if probability >= 0.7:
                prediction = "Likely Approved"
            elif probability >= 0.4:
                prediction = "Uncertain"
            else:
                prediction = "Likely Rejected"
        except Exception as e:
            flash(f"Error making prediction: {str(e)}", 'danger')
            probability = 0.5
            prediction = "Error - Unable to predict"
    
    # Get employee data
    email = session.get('user')
    try:
        employee = get_employee_by_email(email)
    except Exception as e:
        employee = None
        flash(f"Error loading employee data: {str(e)}", 'danger')
    
    return render_template(
        'ai/leave_prediction.html',
        prediction=prediction,
        probability=probability,
        employee=employee
    )

# Employee Attrition Prediction
@ai_routes.route('/attrition_prediction', methods=['GET', 'POST'])
@login_required('admin')
def attrition_prediction():
    """Employee attrition prediction page"""
    if session.get('role') != 'admin':
        flash('Access denied. Admin privileges required.', 'danger')
        return redirect(url_for('employee.dashboard'))
    
    prediction = None
    probability = None
    employee = None
    
    if request.method == 'POST':
        # Get form data
        employee_id = request.form.get('employee_id')
        experience = float(request.form.get('experience', 1.0))
        salary = float(request.form.get('salary', 500000))
        performance_score = float(request.form.get('performance_score', 3.0))
        leaves_taken = int(request.form.get('leaves_taken', 0))
        overtime_hours = int(request.form.get('overtime_hours', 0))
        project_completion = float(request.form.get('project_completion', 0.8))
        satisfaction_score = float(request.form.get('satisfaction_score', 3.0))
        
        # Get employee data
        employee = get_employee_by_id(employee_id)
        
        # Get prediction
        probability = predict_attrition_risk(
            experience, salary, performance_score, leaves_taken,
            overtime_hours, project_completion, satisfaction_score
        )
        
        # Determine prediction text
        if probability >= 0.6:
            prediction = "High Risk"
        else:
            prediction = "Low Risk"
    
    # Get all employees for dropdown
    from models.mongo_models import get_all_employees
    employees = get_all_employees()
    
    return render_template(
        'ai/attrition_prediction.html',
        prediction=prediction,
        probability=probability,
        employee=employee,
        employees=employees
    )

# HR Chatbot
@ai_routes.route('/hr_chatbot', methods=['GET', 'POST'])
@login_required('employee')
def hr_chatbot():
    """HR chatbot page"""
    response = None
    
    if request.method == 'POST':
        query = request.form.get('query', '')
        
        if query:
            # Get chatbot response
            response = get_chatbot_response(query)
    
    return render_template('ai/hr_chatbot.html', response=response)

# API endpoint for chatbot
@ai_routes.route('/api/chatbot', methods=['POST'])
@login_required('employee')
def chatbot_api():
    """API endpoint for HR chatbot"""
    data = request.json
    query = data.get('query', '')
    
    if not query:
        return jsonify({'error': 'Query is required'}), 400
    
    # Get chatbot response
    response = get_chatbot_response(query)
    
    return jsonify({'response': response})

# Initialize sample data for demo
@ai_routes.route('/initialize_demo', methods=['GET'])
@login_required('admin')
def initialize_demo():
    """Initialize demo data for AI features"""
    if session.get('role') != 'admin':
        flash('Access denied. Admin privileges required.', 'danger')
        return redirect(url_for('employee.dashboard'))
    
    # Initialize demo data
    try:
        # Create sample face encodings directory
        os.makedirs('static/images/employees', exist_ok=True)
        success = True
        message = "Demo data structure initialized"
    except Exception as e:
        success = False
        message = str(e)
    
    if success:
        flash("Demo data initialized successfully", 'success')
    else:
        flash(f"Error initializing demo data: {message}", 'danger')
    
    return redirect(url_for('admin.dashboard'))


@ai_routes.route('/camera_attendance_api', methods=['POST'])
@login_required('employee')
def camera_attendance_api():
    """API endpoint to accept a captured image from the browser and perform recognition."""
    data = request.get_json(silent=True)
    if not data:
        return jsonify({'success': False, 'message': 'Invalid request: no JSON data'}), 400

    image_b64 = data.get('image')
    if not image_b64:
        return jsonify({'success': False, 'message': 'Invalid request: no image provided'}), 400

    try:
        # Handle data URL (e.g., "data:image/jpeg;base64,....")
        b64_part = image_b64.split(',', 1)[1] if ',' in image_b64 else image_b64
        image_bytes = np.frombuffer(base64.b64decode(b64_part), dtype=np.uint8)
        frame_bgr = cv2.imdecode(image_bytes, cv2.IMREAD_COLOR)
        if frame_bgr is None:
            return jsonify({'success': False, 'message': 'Failed to decode image'}), 400

        success, message, details = recognize_faces_in_image(frame_bgr)
        return jsonify({'success': success, 'message': message, 'details': details}), 200
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error processing image: {str(e)}'}), 500


@ai_routes.route('/register_face_api', methods=['POST'])
@login_required('admin')
def register_face_api():
    """API endpoint to accept a captured image from the browser and register an employee's face."""
    data = request.get_json(silent=True)
    if not data:
        return jsonify({'success': False, 'message': 'Invalid request: no JSON data'}), 400

    image_b64 = data.get('image')
    employee_id = data.get('employee_id')
    if not image_b64 or not employee_id:
        return jsonify({'success': False, 'message': 'Invalid request: image and employee_id are required'}), 400

    try:
        # Handle data URL (e.g., "data:image/jpeg;base64,....")
        b64_part = image_b64.split(',', 1)[1] if ',' in image_b64 else image_b64
        image_bytes = np.frombuffer(base64.b64decode(b64_part), dtype=np.uint8)
        frame_bgr = cv2.imdecode(image_bytes, cv2.IMREAD_COLOR)
        if frame_bgr is None:
            return jsonify({'success': False, 'message': 'Failed to decode image'}), 400
        
        # Convert to RGB for face_recognition
        import numpy as _np
        frame_rgb = _np.ascontiguousarray(frame_bgr[:, :, ::-1])

        # Save the image to static/images/employees as well
        image_dir = os.path.join('static', 'images', 'employees')
        os.makedirs(image_dir, exist_ok=True)
        image_path = os.path.join(image_dir, f"{employee_id}.jpg")
        cv2.imwrite(image_path, frame_bgr)

        # Encode and save face
        success, message = encode_face(frame_rgb, employee_id, is_array=True)
        return jsonify({'success': success, 'message': message}), 200
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error processing image: {str(e)}'}), 500


@ai_routes.route('/register_own_face_api', methods=['POST'])
@login_required('employee')
def register_own_face_api():
    """API endpoint for employees to register their own face."""
    data = request.get_json(silent=True)
    if not data:
        return jsonify({'success': False, 'message': 'Invalid request: no JSON data'}), 400

    image_b64 = data.get('image')
    if not image_b64:
        return jsonify({'success': False, 'message': 'Invalid request: image is required'}), 400

    try:
        # Get current user's employee_id
        email = session.get('user')
        employee = get_employee_by_email(email)
        if not employee:
            return jsonify({'success': False, 'message': 'Employee not found'}), 404
        employee_id = str(employee['_id'])

        # Handle data URL (e.g., "data:image/jpeg;base64,....")
        b64_part = image_b64.split(',', 1)[1] if ',' in image_b64 else image_b64
        image_bytes = np.frombuffer(base64.b64decode(b64_part), dtype=np.uint8)
        frame_bgr = cv2.imdecode(image_bytes, cv2.IMREAD_COLOR)
        if frame_bgr is None:
            return jsonify({'success': False, 'message': 'Failed to decode image'}), 400
        
        # Convert to RGB for face_recognition
        import numpy as _np
        frame_rgb = _np.ascontiguousarray(frame_bgr[:, :, ::-1])

        # Save the image to static/images/employees as well
        image_dir = os.path.join('static', 'images', 'employees')
        os.makedirs(image_dir, exist_ok=True)
        image_path = os.path.join(image_dir, f"{employee_id}.jpg")
        cv2.imwrite(image_path, frame_bgr)

        # Encode and save face
        success, message = encode_face(frame_rgb, employee_id, is_array=True)
        return jsonify({'success': success, 'message': message}), 200
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error processing image: {str(e)}'}), 500