import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.model_selection import train_test_split
import joblib
import os
from datetime import datetime, timedelta

# Paths for saving models
MODELS_DIR = os.path.join('ai_models', 'saved_models')
os.makedirs(MODELS_DIR, exist_ok=True)

LEAVE_MODEL_PATH = os.path.join(MODELS_DIR, 'leave_model.pkl')
ATTRITION_MODEL_PATH = os.path.join(MODELS_DIR, 'attrition_model.pkl')

# Leave Approval Prediction Model
def train_leave_approval_model(data=None):
    """Train a model to predict leave approval likelihood"""
    if data is None:
        # Generate synthetic data if not provided
        data = generate_synthetic_leave_data()
    
    # Features and target
    X = data[['emergency', 'leave_duration', 'leaves_taken_last_month', 'performance_score', 'department_encoded']]
    y = data['approved']
    
    # Split data
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    # Create and train model
    model = RandomForestClassifier(n_estimators=100, random_state=42)
    model.fit(X_train, y_train)
    
    # Evaluate model
    accuracy = model.score(X_test, y_test)
    print(f"Leave approval model accuracy: {accuracy:.2f}")
    
    # Save model
    joblib.dump(model, LEAVE_MODEL_PATH)
    
    return model, accuracy

def predict_leave_approval(emergency, leave_duration, leaves_taken_last_month, performance_score, department):
    """Predict leave approval likelihood"""
    # Load model if it exists, otherwise train a new one
    if os.path.exists(LEAVE_MODEL_PATH):
        model = joblib.load(LEAVE_MODEL_PATH)
    else:
        model, _ = train_leave_approval_model()
    
    # Department encoding (simplified for demo)
    department_mapping = {
        'HR': 0, 'IT': 1, 'Finance': 2, 'Marketing': 3, 'Operations': 4,
        'Sales': 5, 'Engineering': 6, 'Customer Support': 7, 'Administration': 8
    }
    
    department_encoded = department_mapping.get(department, 0)
    
    # Make prediction
    features = np.array([[emergency, leave_duration, leaves_taken_last_month, performance_score, department_encoded]])
    probability = model.predict_proba(features)[0][1]  # Probability of class 1 (approved)
    
    return probability

# Employee Attrition Prediction Model
def train_attrition_model(data=None):
    """Train a model to predict employee attrition risk"""
    if data is None:
        # Generate synthetic data if not provided
        data = generate_synthetic_attrition_data()
    
    # Features and target
    X = data[['experience', 'salary', 'performance_score', 'leaves_taken', 'overtime_hours', 
              'project_completion', 'satisfaction_score']]
    y = data['attrition_risk']
    
    # Split data
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    # Create and train model
    model = RandomForestClassifier(n_estimators=100, random_state=42)
    model.fit(X_train, y_train)
    
    # Evaluate model
    accuracy = model.score(X_test, y_test)
    print(f"Attrition model accuracy: {accuracy:.2f}")
    
    # Save model
    joblib.dump(model, ATTRITION_MODEL_PATH)
    
    return model, accuracy

def predict_attrition_risk(experience, salary, performance_score, leaves_taken, 
                          overtime_hours, project_completion, satisfaction_score):
    """Predict employee attrition risk"""
    # Load model if it exists, otherwise train a new one
    if os.path.exists(ATTRITION_MODEL_PATH):
        model = joblib.load(ATTRITION_MODEL_PATH)
    else:
        model, _ = train_attrition_model()
    
    # Make prediction
    features = np.array([[experience, salary, performance_score, leaves_taken, 
                         overtime_hours, project_completion, satisfaction_score]])
    probability = model.predict_proba(features)[0][1]  # Probability of class 1 (high risk)
    
    return probability

# Synthetic Data Generation
def generate_synthetic_leave_data(n_samples=1000):
    """Generate synthetic data for leave approval prediction"""
    np.random.seed(42)
    
    # Generate features
    emergency = np.random.choice([0, 1], size=n_samples, p=[0.8, 0.2])  # 0: No, 1: Yes
    leave_duration = np.random.randint(1, 15, size=n_samples)  # 1-14 days
    leaves_taken_last_month = np.random.randint(0, 5, size=n_samples)  # 0-4 leaves
    performance_score = np.random.uniform(2.0, 5.0, size=n_samples)  # 2.0-5.0 score
    department_encoded = np.random.randint(0, 9, size=n_samples)  # 0-8 departments
    
    # Generate target based on rules
    approved = np.zeros(n_samples, dtype=int)
    
    for i in range(n_samples):
        # Higher chance of approval for emergencies
        if emergency[i] == 1:
            approval_chance = 0.9
        else:
            # Lower chance for longer leaves
            if leave_duration[i] > 7:
                approval_chance = 0.5
            else:
                approval_chance = 0.8
            
            # Reduce chance if many leaves taken recently
            if leaves_taken_last_month[i] >= 3:
                approval_chance -= 0.3
            
            # Increase chance for high performers
            if performance_score[i] >= 4.0:
                approval_chance += 0.2
        
        # Ensure probability is between 0 and 1
        approval_chance = max(0.1, min(0.95, approval_chance))
        
        # Determine approval
        approved[i] = np.random.choice([0, 1], p=[1-approval_chance, approval_chance])
    
    # Create DataFrame
    df = pd.DataFrame({
        'emergency': emergency,
        'leave_duration': leave_duration,
        'leaves_taken_last_month': leaves_taken_last_month,
        'performance_score': performance_score,
        'department_encoded': department_encoded,
        'approved': approved
    })
    
    return df

def generate_synthetic_attrition_data(n_samples=1000):
    """Generate synthetic data for employee attrition prediction"""
    np.random.seed(42)
    
    # Generate features
    experience = np.random.uniform(0.5, 15.0, size=n_samples)  # 0.5-15 years
    salary = np.random.uniform(300000, 2500000, size=n_samples)  # 3-25 lakhs
    performance_score = np.random.uniform(2.0, 5.0, size=n_samples)  # 2.0-5.0 score
    leaves_taken = np.random.randint(0, 25, size=n_samples)  # 0-24 leaves per year
    overtime_hours = np.random.randint(0, 100, size=n_samples)  # 0-99 hours per month
    project_completion = np.random.uniform(0.7, 1.0, size=n_samples)  # 70-100% completion rate
    satisfaction_score = np.random.uniform(1.0, 5.0, size=n_samples)  # 1.0-5.0 satisfaction
    
    # Generate target based on rules
    attrition_risk = np.zeros(n_samples, dtype=int)
    
    for i in range(n_samples):
        risk_score = 0
        
        # Low experience often means higher attrition
        if experience[i] < 2:
            risk_score += 2
        elif experience[i] > 10:
            risk_score -= 1
        
        # Low salary increases risk
        if salary[i] < 600000:
            risk_score += 2
        elif salary[i] > 1500000:
            risk_score -= 1
        
        # Low performance increases risk
        if performance_score[i] < 3.0:
            risk_score += 2
        elif performance_score[i] >= 4.5:
            risk_score -= 1
        
        # Many leaves might indicate dissatisfaction
        if leaves_taken[i] > 15:
            risk_score += 1
        
        # High overtime might cause burnout
        if overtime_hours[i] > 60:
            risk_score += 2
        
        # Low project completion rate might indicate disengagement
        if project_completion[i] < 0.8:
            risk_score += 1
        
        # Low satisfaction is a strong indicator
        if satisfaction_score[i] < 2.5:
            risk_score += 3
        elif satisfaction_score[i] >= 4.0:
            risk_score -= 2
        
        # Determine risk category (high risk if score > 2)
        attrition_risk[i] = 1 if risk_score > 2 else 0
    
    # Create DataFrame
    df = pd.DataFrame({
        'experience': experience,
        'salary': salary,
        'performance_score': performance_score,
        'leaves_taken': leaves_taken,
        'overtime_hours': overtime_hours,
        'project_completion': project_completion,
        'satisfaction_score': satisfaction_score,
        'attrition_risk': attrition_risk
    })
    
    return df

# Initialize models
def initialize_models():
    """Initialize and train models if they don't exist"""
    if not os.path.exists(LEAVE_MODEL_PATH):
        train_leave_approval_model()
    
    if not os.path.exists(ATTRITION_MODEL_PATH):
        train_attrition_model()
    
    return True