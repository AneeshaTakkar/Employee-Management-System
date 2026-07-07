import bcrypt
import random
import numpy as np
from datetime import datetime, timedelta
from pymongo import MongoClient
import os
from dotenv import load_dotenv
from PIL import Image

# Try to import face recognition
try:
    import face_recognition
    FR_AVAILABLE = True
except ImportError:
    FR_AVAILABLE = False
    print("[INFO] face_recognition not available, using random encodings")

load_dotenv()

MONGO_URI = os.environ.get("MONGO_URI", "mongodb://localhost:27017/ems_pro")

client = MongoClient(MONGO_URI)
db = client.get_database()

print("Connected to MongoDB successfully!")

def hash_password(password):
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

# Clear existing data
db.users.delete_many({'role': 'employee'})
db.attendance.delete_many({})
db.leaves.delete_many({})
db.face_encodings.delete_many({})
print("[INFO] Cleared existing employees, attendance, leaves, and face encodings!")

# Create admin user
admin_data = {
    'name': 'Admin User',
    'email': 'admin@example.com',
    'password': hash_password('admin123'),
    'role': 'admin',
    'created_at': datetime.now(),
    'active': True,
    'department': 'Administration'
}

if not db.users.find_one({'email': admin_data['email']}):
    db.users.insert_one(admin_data)
    print("[OK] Admin user created successfully!")
else:
    print("[INFO] Admin user already exists!")

# Path to employee images
EMPLOYEE_IMAGES_DIR = os.path.join(os.path.dirname(__file__), 'static', 'images', 'employees')

# List of available sample images
sample_image_files = []
if os.path.exists(EMPLOYEE_IMAGES_DIR):
    sample_image_files = [
        f for f in os.listdir(EMPLOYEE_IMAGES_DIR)
        if f.lower().endswith(('.jpg', '.jpeg', '.png'))
    ]
    print(f"[INFO] Found {len(sample_image_files)} sample employee images")

# Create 20 sample employees
departments = ['Engineering', 'Marketing', 'Sales', 'HR', 'Finance']
sample_employees = []
employee_ids = []

for i in range(1, 21):
    emp_num = str(i)
    # Try to get a sample image for this employee
    image_file = None
    if sample_image_files:
        image_idx = (i - 1) % len(sample_image_files)
        image_file = sample_image_files[image_idx]
    
    sample_employees.append({
        'name': f'Employee {emp_num}',
        'email': f'employee{emp_num}@example.com',
        'password': 'employee123',
        'department': departments[(i - 1) % 5],
        'image_file': image_file
    })

for emp in sample_employees:
    if not db.users.find_one({'email': emp['email']}):
        emp_data = {
            'name': emp['name'],
            'email': emp['email'],
            'password': hash_password(emp['password']),
            'role': 'employee',
            'created_at': datetime.now(),
            'active': True,
            'department': emp['department']
        }
        result = db.users.insert_one(emp_data)
        employee_ids.append(result.inserted_id)
        print(f"[OK] Employee {emp['name']} created! (ID: {result.inserted_id})")
    else:
        existing_emp = db.users.find_one({'email': emp['email']})
        employee_ids.append(existing_emp['_id'])
        print(f"[INFO] Employee {emp['name']} already exists! (ID: {existing_emp['_id']})")

# Add sample face encodings for all employees
print("\nAdding sample face encodings...")
for emp_idx, emp in enumerate(sample_employees):
    emp_id = employee_ids[emp_idx]
    encoding = None
    
    if FR_AVAILABLE and emp['image_file']:
        # Try to encode from sample image
        image_path = os.path.join(EMPLOYEE_IMAGES_DIR, emp['image_file'])
        try:
            image = face_recognition.load_image_file(image_path)
            face_locations = face_recognition.face_locations(image)
            if face_locations:
                encodings = face_recognition.face_encodings(image, face_locations)
                if encodings:
                    encoding = encodings[0].tolist()
                    print(f"[OK] Encoded {emp['name']} from {emp['image_file']}")
        except Exception as e:
            print(f"[WARN] Could not encode {emp['name']} from image: {e}")
    
    if encoding is None:
        # Generate random encoding
        random_encoding = np.random.uniform(low=-1, high=1, size=(128,))
        random_encoding = random_encoding / np.linalg.norm(random_encoding)
        encoding = random_encoding.tolist()
        print(f"[OK] Generated random encoding for {emp['name']}")
    
    # Save to DB
    db.face_encodings.update_one(
        {'employee_id': emp_id},
        {'$set': {
            'encoding': encoding,
            'updated_at': datetime.now()
        }},
        upsert=True
    )

# Add random attendance records for the past 30 days
print("\nAdding attendance records...")
today = datetime.now()
statuses = ['Present', 'Absent', 'Late']

for emp_idx, emp in enumerate(sample_employees):
    emp_id = employee_ids[emp_idx]
    for day_offset in range(30):
        date = today - timedelta(days=day_offset)
        status = random.choices(statuses, weights=[0.75, 0.1, 0.15])[0]
        
        attendance_record = {
            'employee_id': emp_id,
            'email': emp['email'],
            'date': date.strftime('%Y-%m-%d'),
            'timestamp': date.replace(hour=random.randint(8, 10), minute=random.randint(0, 59)),
            'status': status,
            'method': 'Manual'
        }
        db.attendance.insert_one(attendance_record)
    print(f"[OK] Added 30 days of attendance for {emp['name']}")

# Add random leave records
print("\nAdding leave records...")
leave_types = ['Sick Leave', 'Annual Leave', 'Personal Leave', 'Other']
leave_statuses = ['Approved', 'Pending', 'Rejected']

for emp_idx, emp in enumerate(sample_employees):
    num_leaves = random.randint(1, 5)
    for _ in range(num_leaves):
        start_offset = random.randint(1, 60)
        duration = random.randint(1, 3)
        start_date = today - timedelta(days=start_offset)
        end_date = start_date + timedelta(days=duration)
        
        leave_record = {
            'email': emp['email'],
            'reason': f"{random.choice(leave_types)} request",
            'from_date': start_date.strftime('%Y-%m-%d'),
            'to_date': end_date.strftime('%Y-%m-%d'),
            'leave_type': random.choice(leave_types),
            'emergency': random.choice([True, False]),
            'status': random.choices(leave_statuses, weights=[0.6, 0.25, 0.15])[0],
            'applied_at': start_date - timedelta(days=random.randint(1, 5))
        }
        db.leaves.insert_one(leave_record)
    print(f"[OK] Added {num_leaves} leave(s) for {emp['name']}")

print("\nDatabase seeding completed!")
print(f"\nAdmin Login:")
print(f"  Email: admin@example.com")
print(f"  Password: admin123")
print(f"\nEmployee Login (all use same password):")
print(f"  Password: employee123")
print(f"\nEmployee List (for face registration):")
for emp_idx, emp in enumerate(sample_employees):
    print(f"  {emp['name']}: ID={employee_ids[emp_idx]}")
print(f"\n{'NOTE: ' if not FR_AVAILABLE else ''}{'Some ' if FR_AVAILABLE else 'All '}face encodings are random!")
print(f"To use real face recognition, install face_recognition and upload employee photos!")
