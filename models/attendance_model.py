from mongoengine import Document, ReferenceField, DateTimeField, StringField
from models.user_model import User  # Adjust path if needed
from datetime import datetime

class Attendance(Document):
    user = ReferenceField(User, required=True)
    date = DateTimeField(default=datetime.now)
    status = StringField(required=True, choices=["Present", "Absent", "Leave"])
