from mongoengine import Document, ReferenceField, StringField, DateTimeField
from datetime import datetime

class Leave(Document):
    user = ReferenceField('User', required=True)
    reason = StringField(required=True)
    status = StringField(default="Pending")
    applied_on = DateTimeField(default=datetime.utcnow)
