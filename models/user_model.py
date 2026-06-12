from bson import ObjectId
from mongoengine import Document, StringField, DateTimeField

class User(Document):
    name = StringField(required=True)
    email = StringField(required=True, unique=True)
    password = StringField(required=True)
    role = StringField(required=True, choices=["admin", "employee"])
    department = StringField()
    designation = StringField()
    join_date = DateTimeField()
