# Try to import face_recognition, but provide fallbacks if available
try:
    import face_recognition
    FACE_RECOGNITION_AVAILABLE = True
    print("✅ Face recognition is available and working!")
except ImportError as e:
    FACE_RECOGNITION_AVAILABLE = False
    print(f"Warning: face_recognition module not available ({str(e)}). Face recognition features will be disabled.")

import cv2
import numpy as np
from datetime import datetime
import os
import pickle
from models.mongo_models import save_face_encoding, get_all_face_encodings, save_camera_attendance, get_employee_by_id

# Directory to store employee face images
FACE_IMAGES_DIR = os.path.join('static', 'images', 'employees')

# Ensure directory exists
os.makedirs(FACE_IMAGES_DIR, exist_ok=True)

# Helper: import face_recognition at runtime to avoid stale availability flags
def _import_fr():
    try:
        import face_recognition as fr
        print("[DEBUG] Runtime import of face_recognition succeeded")
        return fr
    except ImportError as e:
        # Fallback: if module-level import already succeeded, reuse it
        try:
            if FACE_RECOGNITION_AVAILABLE and 'face_recognition' in globals():
                print("[DEBUG] Using module-level face_recognition instance")
                return face_recognition
            import sys
            fr = sys.modules.get('face_recognition')
            if fr is not None:
                print("[DEBUG] Using face_recognition from sys.modules")
                return fr
        except Exception as _e:
            print(f"[DEBUG] Fallback to globals/sys.modules failed: {_e}")
        print(f"[DEBUG] face_recognition import failed at runtime: {e}")
        return None

def encode_face(image_path, employee_id):
    """Encode a face from an image file and save to MongoDB"""
    fr = _import_fr()
    if fr is None:
        return False, "Face recognition is not available. Please install the required libraries."
        
    try:
        # Load via PIL to guarantee 8-bit RGB
        import numpy as _np
        from PIL import Image as _PILImage
        pil = _PILImage.open(image_path).convert('RGB')
        image = _np.ascontiguousarray(_np.array(pil, dtype=_np.uint8))
        # Find face locations in the image
        face_locations = fr.face_locations(image)
        
        if not face_locations:
            return False, "No face detected in the image"
        
        # Get face encodings
        face_encodings = fr.face_encodings(image, face_locations)
        
        if not face_encodings:
            return False, "Could not encode the face"
        
        # Save the first face encoding to MongoDB
        save_face_encoding(employee_id, face_encodings[0])
        
        return True, "Face encoded successfully"
    except Exception as e:
        return False, f"Error encoding face: {str(e)}"

def recognize_faces_from_camera():
    """Recognize faces from camera feed and mark attendance"""
    fr = _import_fr()
    if fr is None:
        print("[DEBUG] FR unavailable at runtime, returning not available message")
        return False, "Face recognition is not available. Please install the required libraries."
        
    try:
        print(f"[DEBUG] OpenCV version: {cv2.__version__}")
        # Get all face encodings from MongoDB
        stored_encodings = get_all_face_encodings()
        
        if not stored_encodings:
            print("[DEBUG] No stored encodings found in DB")
            return False, "No face encodings found in the database"
        
        # Extract employee IDs and encodings
        known_face_encodings = []
        known_face_ids = []
        
        for entry in stored_encodings:
            # Convert list to numpy array if needed
            if isinstance(entry['encoding'], list):
                known_face_encodings.append(np.array(entry['encoding']))
            else:
                known_face_encodings.append(entry['encoding'])
            known_face_ids.append(str(entry['employee_id']))
        
        # Initialize webcam
        video_capture = cv2.VideoCapture(0)
        
        # Track which employees have been marked present
        marked_attendance = set()
        
        # Process frames until 'q' is pressed
        while True:
            # Grab a single frame of video
            ret, frame = video_capture.read()
            
            if not ret:
                break
                
            # Convert the image from BGR color (OpenCV) to RGB color (face_recognition)
            rgb_frame = np.ascontiguousarray(frame[:, :, ::-1])
            
            # Find all the faces and face encodings in the current frame
            face_locations = fr.face_locations(rgb_frame)
            face_encodings = fr.face_encodings(rgb_frame, face_locations)
            
            # Loop through each face found in the frame
            for (top, right, bottom, left), face_encoding in zip(face_locations, face_encodings):
                # See if the face matches any known faces
                matches = fr.compare_faces(known_face_encodings, face_encoding)
                name = "Unknown"
                
                # Use the known face with the smallest distance to the new face
                face_distances = fr.face_distance(known_face_encodings, face_encoding)
                best_match_index = np.argmin(face_distances)
                
                if matches[best_match_index]:
                    employee_id = known_face_ids[best_match_index]
                    employee = get_employee_by_id(employee_id)
                    
                    if employee:
                        name = employee.get('name', 'Unknown')
                        
                        # Mark attendance if not already marked
                        if employee_id not in marked_attendance:
                            save_camera_attendance(employee_id)
                            marked_attendance.add(employee_id)
                
                # Draw a box around the face
                cv2.rectangle(frame, (left, top), (right, bottom), (0, 255, 0), 2)
                
                # Draw a label with a name below the face
                cv2.rectangle(frame, (left, bottom - 35), (right, bottom), (0, 255, 0), cv2.FILLED)
                font = cv2.FONT_HERSHEY_DUPLEX
                cv2.putText(frame, name, (left + 6, bottom - 6), font, 1.0, (255, 255, 255), 1)
            
            # Display the resulting image
            cv2.imshow('Camera Attendance System', frame)
            
            # Hit 'q' on the keyboard to quit
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
        
        # Release the webcam and close windows
        video_capture.release()
        cv2.destroyAllWindows()
        
        return True, f"Marked attendance for {len(marked_attendance)} employees"
    except Exception as e:
        print(f"[DEBUG] Exception in recognize_faces_from_camera: {e}")
        return False, f"Error recognizing faces: {str(e)}"

def generate_sample_encodings():
    """Generate sample face encodings for demo purposes"""
    if not FACE_RECOGNITION_AVAILABLE:
        # Generate random encodings if face_recognition is not available
        employee_ids = ['60d21b4667d0d8992e610c85', '60d21b4667d0d8992e610c86', '60d21b4667d0d8992e610c87']
        
        for emp_id in employee_ids:
            # Generate a random 128-dimensional face encoding
            random_encoding = np.random.uniform(low=-1, high=1, size=(128,))
            
            # Normalize the encoding to have unit length
            random_encoding = random_encoding / np.linalg.norm(random_encoding)
            
            # Save to MongoDB
            save_face_encoding(emp_id, random_encoding)
        
        return True, f"Generated sample encodings for {len(employee_ids)} employees"
    
    # If face_recognition is available, use the original method
    try:
        # Sample employee IDs and their stock images
        sample_employees = [
            {'id': '60d21b4667d0d8992e610c85', 'name': 'Rahul Sharma', 'image': 'employee1.jpg'},
            {'id': '60d21b4667d0d8992e610c86', 'name': 'Priya Patel', 'image': 'employee2.jpg'},
            {'id': '60d21b4667d0d8992e610c87', 'name': 'Amit Singh', 'image': 'employee3.jpg'},
            {'id': '60d21b4667d0d8992e610c88', 'name': 'Neha Gupta', 'image': 'employee4.jpg'},
            {'id': '60d21b4667d0d8992e610c89', 'name': 'Vikram Malhotra', 'image': 'employee5.jpg'}
        ]
        
        for employee in sample_employees:
            image_path = os.path.join(FACE_IMAGES_DIR, employee['image'])
            
            # Skip if image doesn't exist
            if not os.path.exists(image_path):
                continue
                
            # Encode and save face
            success, message = encode_face(image_path, employee['id'])
            print(f"Encoded {employee['name']}: {message}")
        
        return True, "Sample encodings generated successfully"
    except Exception as e:
        return False, f"Error generating sample encodings: {str(e)}"


def recognize_faces_in_image(image_bgr):
    """Recognize faces in a single BGR image frame from the browser and mark attendance.
    Returns: (success: bool, message: str, details: dict)
    """
    fr = _import_fr()
    if fr is None:
        return False, "Face recognition is not available. Please install the required libraries.", {}

    try:
        # Load stored encodings
        stored_encodings = get_all_face_encodings()
        if not stored_encodings:
            return False, "No face encodings found in the database", {}

        known_face_encodings = []
        known_face_ids = []
        for entry in stored_encodings:
            enc = np.array(entry['encoding']) if isinstance(entry['encoding'], list) else entry['encoding']
            known_face_encodings.append(enc)
            known_face_ids.append(str(entry['employee_id']))

        # Convert to RGB for face_recognition and ensure contiguous memory
        rgb_frame = np.ascontiguousarray(image_bgr[:, :, ::-1])

        # Detect faces and compute encodings
        face_locations = fr.face_locations(rgb_frame)
        face_encodings = fr.face_encodings(rgb_frame, face_locations)

        recognized = []
        marked_attendance = set()

        for face_encoding in face_encodings:
            matches = fr.compare_faces(known_face_encodings, face_encoding)
            if len(known_face_encodings) == 0:
                continue
            face_distances = fr.face_distance(known_face_encodings, face_encoding)
            best_match_index = int(np.argmin(face_distances)) if len(face_distances) else None

            if best_match_index is not None and matches[best_match_index]:
                employee_id = known_face_ids[best_match_index]
                employee = get_employee_by_id(employee_id)
                name = employee.get('name', 'Unknown') if employee else 'Unknown'
                recognized.append({'employee_id': employee_id, 'name': name})

                if employee_id not in marked_attendance:
                    save_camera_attendance(employee_id)
                    marked_attendance.add(employee_id)

        if not face_encodings:
            return False, "No faces detected in the image", {'recognized': [], 'count': 0}

        message = (
            f"Marked attendance for {len(marked_attendance)} employees" if marked_attendance
            else "No known faces recognized"
        )
        return True, message, {'recognized': recognized, 'count': len(marked_attendance)}
    except Exception as e:
        return False, f"Error recognizing faces: {str(e)}", {}