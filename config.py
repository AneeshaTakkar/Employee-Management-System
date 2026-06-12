import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "5f6b14f3c6a74e9a8d2e814f71fbbc90")
    SESSION_TYPE = "filesystem"
    MONGO_URI = os.environ.get("MONGO_URI", "mongodb://localhost:27017/ems_pro")
