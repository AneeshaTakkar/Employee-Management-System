# Employee Management System (EMS) - Academic Project

A comprehensive Employee Management System built with Flask and MongoDB, featuring AI capabilities including face recognition attendance, HR chatbot, and ML-based attrition prediction.

## 🚀 Deployment Guide

### Prerequisites
- GitHub account
- Render account (free tier)
- MongoDB Atlas account (free tier)

### Step 1: Set up MongoDB Atlas

1. Go to [MongoDB Atlas](https://www.mongodb.com/cloud/atlas) and create a free account
2. Create a new cluster (free tier M0)
3. Create a database user with username/password
4. Network Access: Allow access from anywhere (0.0.0.0/0) for testing
5. Get your connection string from "Connect" → "Connect your application"
6. Format: `mongodb+srv://<username>:<password>@cluster0.xxxxx.mongodb.net/ems_pro?retryWrites=true&w=majority`

### Step 2: Push to GitHub

1. Create a new repository on GitHub
2. Initialize git in your project folder:
```bash
git init
git add .
git commit -m "Initial commit"
```

3. Add your GitHub repository as remote:
```bash
git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO_NAME.git
```

4. Push to GitHub:
```bash
git branch -M main
git push -u origin main
```

### Step 3: Deploy to Render

1. Go to [Render](https://render.com) and create a free account
2. Click "New +" → "Web Service"
3. Connect your GitHub account and select this repository
4. Configure:
   - **Name**: ems-pro (or any name)
   - **Environment**: Python 3
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn app:app`
5. Add Environment Variables:
   - `MONGO_URI`: Your MongoDB Atlas connection string
   - `SECRET_KEY`: Generate a random secret key (use: `python -c "import secrets; print(secrets.token_hex(32))"`)
   - `OPENAI_API_KEY`: Your OpenAI API key (if using AI features)
6. Click "Create Web Service"
7. Wait for deployment (5-10 minutes)
8. Your app will be available at: `https://your-app-name.onrender.com`

## 📁 Project Structure

```
EMS-Pro-Version/
├── app.py                 # Main Flask application
├── config.py              # Configuration settings
├── requirements.txt       # Python dependencies
├── Procfile              # Render deployment configuration
├── .gitignore            # Git ignore rules
├── models/               # MongoDB models
├── routes/               # Flask routes (auth, admin, employee, public, ai)
├── templates/            # Jinja2 HTML templates
├── static/               # CSS, JS, images
├── ai_models/            # AI/ML models
└── utils/                # Utility functions
```

## 🔧 Local Development

1. Create virtual environment:
```bash
python -m venv venv
venv\Scripts\activate  # Windows
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up environment variables in `.env`:
```
MONGO_URI=mongodb://localhost:27017/ems_pro
SECRET_KEY=your-secret-key
OPENAI_API_KEY=your-api-key
```

4. Run the application:
```bash
python app.py
```

5. Access at: `http://localhost:5000`

## 🎯 Features

- User authentication (Admin, Employee)
- Employee management (CRUD operations)
- Face recognition attendance system
- HR chatbot with AI
- ML-based attrition prediction
- Public dashboard
- Admin analytics dashboard

## 📝 Notes

- This is a server-side rendered Flask application (not a separate frontend/backend architecture)
- The entire app is deployed as a single unit on Render
- MongoDB Atlas provides the cloud database
- Free tiers are sufficient for academic purposes

## 🆘 Troubleshooting

- If deployment fails, check Render logs
- Ensure MongoDB Atlas IP whitelist allows all IPs (0.0.0.0/0)
- Verify all environment variables are set correctly in Render
- Make sure your MongoDB connection string includes the database name
