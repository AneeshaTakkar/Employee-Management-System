import cv2
import numpy as np
from datetime import datetime
import os
from models.mongo_models import save_face_encoding, get_all_face_encodings, save_camera_attendance, get_employee_by_id
from deepface import DeepFace

# Directory to store employee face images
FACE_IMAGES_DIR = os.path.join('static', 'images', 'employees')

# Ensure directory exists
os.makedirs(FACE_IMAGES_DIR, exist_ok=True)


def encode_face(image_path_or_array, employee_id, is_array=False):
    """Encode a face from an image file or numpy array and save to MongoDB"""
    try:
        if is_array:
            # Convert numpy array to temp file (DeepFace works better with files or RGB arrays)
            temp_path = os.path.join(FACE_IMAGES_DIR, f"temp_{employee_id}.jpg")
            cv2.imwrite(temp_path, image_path_or_array)
            image_path = temp_path
        else:
            image_path = image_path_or_array

        # Use DeepFace to get face encoding
        embedding = DeepFace.represent(
            img_path=image_path,
            model_name="Facenet512",
            enforce_detection=True,
            detector_backend="opencv"
        )[0]["embedding"]

        # Save the embedding to MongoDB
        save_face_encoding(employee_id, embedding)

        if is_array:
            # Clean up temp file
            os.remove(temp_path)

        return True, "Face encoded successfully"
    except Exception as e:
        return False, f"Error encoding face: {str(e)}"


def recognize_faces_from_camera():
    """Recognize faces from camera feed and mark attendance"""
    try:
        # Get all face encodings from MongoDB
        stored_encodings = get_all_face_encodings()

        if not stored_encodings:
            return False, "No face encodings found in the database"

        # Extract employee IDs and encodings
        known_face_encodings = []
        known_face_ids = []

        for entry in stored_encodings:
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

            # Save frame temporarily for DeepFace
            temp_frame_path = os.path.join(FACE_IMAGES_DIR, "temp_frame.jpg")
            cv2.imwrite(temp_frame_path, frame)

            try:
                # Use DeepFace to find faces in the frame
                results = DeepFace.find(
                    img_path=temp_frame_path,
                    db_path=FACE_IMAGES_DIR,
                    model_name="Facenet512",
                    enforce_detection=False,
                    detector_backend="opencv"
                )

                for _, row in results[0].iterrows():
                    # Extract employee ID from the file path (filename is employee_id.jpg)
                    file_name = os.path.basename(row['identity'])
                    employee_id = os.path.splitext(file_name)[0]

                    if employee_id in known_face_ids and employee_id not in marked_attendance:
                        employee = get_employee_by_id(employee_id)
                        if employee:
                            save_camera_attendance(employee_id)
                            marked_attendance.add(employee_id)

                            # Draw a box around the face
                            x1, y1, x2, y2 = int(row['source_x']), int(row['source_y']), int(row['source_x'] + row['source_w']), int(row['source_y'] + row['source_h'])
                            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                            cv2.putText(frame, employee.get('name', 'Unknown'), (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 0), 2)
            except Exception:
                pass  # No face found, continue

            # Display the resulting image
            cv2.imshow('Camera Attendance System', frame)

            # Hit 'q' on the keyboard to quit
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

        # Clean up
        if os.path.exists(temp_frame_path):
            os.remove(temp_frame_path)
        video_capture.release()
        cv2.destroyAllWindows()

        return True, f"Marked attendance for {len(marked_attendance)} employees"
    except Exception as e:
        print(f"[DEBUG] Exception in recognize_faces_from_camera: {e}")
        return False, f"Error recognizing faces: {str(e)}"


def generate_sample_encodings():
    """Generate sample face encodings for demo purposes"""
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

        # Save temp image for DeepFace
        temp_path = os.path.join(FACE_IMAGES_DIR, "temp_recognize.jpg")
        cv2.imwrite(temp_path, image_bgr)

        recognized = []
        marked_attendance = set()

        try:
            # Find faces in image
            results = DeepFace.find(
                img_path=temp_path,
                db_path=FACE_IMAGES_DIR,
                model_name="Facenet512",
                enforce_detection=False,
                detector_backend="opencv"
            )

            for _, row in results[0].iterrows():
                file_name = os.path.basename(row['identity'])
                employee_id = os.path.splitext(file_name)[0]

                if employee_id in known_face_ids and employee_id not in marked_attendance:
                    employee = get_employee_by_id(employee_id)
                    name = employee.get('name', 'Unknown') if employee else 'Unknown'
                    recognized.append({'employee_id': employee_id, 'name': name})
                    save_camera_attendance(employee_id)
                    marked_attendance.add(employee_id)
        except Exception:
            pass  # No face found

        # Clean up temp file
        if os.path.exists(temp_path):
            os.remove(temp_path)

        if not recognized:
            return False, "No known faces recognized", {'recognized': [], 'count': 0}

        message = f"Marked attendance for {len(marked_attendance)} employees"
        return True, message, {'recognized': recognized, 'count': len(marked_attendance)}
    except Exception as e:
        return False, f"Error recognizing faces: {str(e)}", {}
