TO START:
    python app.py
    
LOGIN CREDENTIALS:
    Admin Login:
    Email: admin@example.com
    Password: admin123

    Employee Login:
    Email: employee@example.com
    Password: employee123

VIRTUAL ENVIRONMENT:
    - Press Ctrl+Shift+P
    - Type “Python: Select Interpreter”
    - Choose the interpreter from your project’s venv ( c:\Users\anika\OneDrive\Desktop\EMS-Pro-Version\venv\Scripts\python.exe)

Create and use a single virtual environment (recommended: venv)
    - Create venv using system Python:
    - python -m venv venv
    - Activate it in PowerShell:
    - venv\Scripts\Activate.ps1

For “Employee ID”, use a valid MongoDB ObjectID of an employee. If you’re using the default user employee@example.com , you can get the _id with:
    - venv\Scripts\python.exe -c "from pymongo import MongoClient;print(MongoClient('mongodb://localhost:27017/ems_pro').get_database().users.find_one({'email':'employee@example.com'})['_id'])"
    689cc398c6970e7798f3fa9b

