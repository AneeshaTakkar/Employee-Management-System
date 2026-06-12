import os

# Try to import OpenAI, but provide fallbacks if not available
try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    print("Warning: OpenAI module not available. Chatbot will use fallback responses.")

from models.mongo_models import get_hr_faq

# Set OpenAI API key from environment variable
openai_api_key = os.environ.get('OPENAI_API_KEY', 'your-api-key-here')

# Initialize OpenAI client if available
client = None
if OPENAI_AVAILABLE and openai_api_key and openai_api_key != 'your-api-key-here':
    try:
        client = OpenAI(api_key=openai_api_key)
    except Exception as e:
        print(f"Error initializing OpenAI client: {e}")
        OPENAI_AVAILABLE = False

# Default HR policies and information
DEFAULT_HR_POLICIES = """
Leave Policy:
- Each employee is entitled to 24 paid leaves per year.
- Leaves must be applied at least 3 days in advance, except for emergencies.
- Unused leaves can be carried forward to the next year (max 12 leaves).

Holidays:
- New Year's Day (January 1)
- Republic Day (January 26)
- Holi (March, varies)
- Good Friday (April, varies)
- Independence Day (August 15)
- Gandhi Jayanti (October 2)
- Diwali (October/November, varies)
- Christmas (December 25)

Benefits:
- Health insurance coverage for employee and dependents
- Provident Fund contribution
- Annual performance bonus
- Professional development allowance
- Flexible work hours
- Work from home option (twice a week)

Work Hours:
- Monday to Friday, 9:00 AM to 6:00 PM
- 1-hour lunch break
- Weekend offs (Saturday and Sunday)
"""

def get_chatbot_response(query, use_openai=True):
    """Get response from HR chatbot"""
    # First check if we have the answer in our FAQ database
    faq_entries = get_hr_faq()
    
    # Convert query to lowercase for case-insensitive matching
    query_lower = query.lower()
    
    # Try to find a matching FAQ
    for entry in faq_entries:
        if query_lower in entry['question'].lower():
            return entry['answer']
    
    # If no match found in FAQ and OpenAI is available and enabled, use OpenAI API
    if use_openai and OPENAI_AVAILABLE and client and openai_api_key and openai_api_key != 'your-api-key-here':
        try:
            # Create context with HR policies
            context = f"HR Policies and Information:\n{DEFAULT_HR_POLICIES}\n\nEmployee Question: {query}\n\nHR Assistant:"
            
            # Call OpenAI API using the client
            response = client.completions.create(
                model="gpt-3.5-turbo-instruct",  # Updated model name
                prompt=context,
                max_tokens=150,
                temperature=0.7,
                top_p=1.0,
                frequency_penalty=0.0,
                presence_penalty=0.0
            )
            
            return response.choices[0].text.strip()
            
        except Exception as e:
            print(f"OpenAI API error: {e}")
            return fallback_response(query)
    
    # Fallback to rule-based responses
    return fallback_response(query)

def fallback_response(query):
    """Generate a rule-based response when API is not available"""
    query_lower = query.lower()
    
    # Leave-related queries
    if any(keyword in query_lower for keyword in ['leave', 'vacation', 'time off', 'sick', 'absent']):
        return "Each employee is entitled to 24 paid leaves per year. Leaves should be applied at least 3 days in advance, except for emergencies. You can apply for leave through your employee dashboard."
    
    # Holiday-related queries
    elif any(keyword in query_lower for keyword in ['holiday', 'festival', 'celebration', 'day off']):
        return "We observe 8 holidays per year including New Year's Day, Republic Day, Holi, Good Friday, Independence Day, Gandhi Jayanti, Diwali, and Christmas. Check the company calendar for exact dates."
    
    # Benefits-related queries
    elif any(keyword in query_lower for keyword in ['benefit', 'insurance', 'medical', 'health', 'bonus', 'allowance']):
        return "Our benefits include health insurance for you and your dependents, provident fund contribution, annual performance bonus, and professional development allowance. Contact HR for more details."
    
    # Work hours-related queries
    elif any(keyword in query_lower for keyword in ['work hour', 'timing', 'schedule', 'working day', 'weekend']):
        return "Our work hours are Monday to Friday, 9:00 AM to 6:00 PM with a 1-hour lunch break. We have weekend offs on Saturday and Sunday."
    
    # Salary-related queries
    elif any(keyword in query_lower for keyword in ['salary', 'pay', 'compensation', 'increment', 'raise']):
        return "Salaries are credited on the last working day of each month. Annual increments are based on performance reviews conducted in March."
    
    # Default response
    else:
        return "I'm not sure about that. Please contact the HR department for more information or check the employee handbook."

# Sample FAQ data for initialization
SAMPLE_FAQ = [
    {
        "question": "How many leaves do I get per year?",
        "answer": "Each employee is entitled to 24 paid leaves per year. This includes casual leaves, sick leaves, and earned leaves."
    },
    {
        "question": "What are the working hours?",
        "answer": "The standard working hours are Monday to Friday, 9:00 AM to 6:00 PM with a 1-hour lunch break."
    },
    {
        "question": "How do I apply for leave?",
        "answer": "You can apply for leave through your employee dashboard. Go to the 'Leave' section and fill out the leave application form."
    },
    {
        "question": "When is the salary credited?",
        "answer": "Salaries are credited on the last working day of each month."
    },
    {
        "question": "What is the health insurance coverage?",
        "answer": "The company provides health insurance coverage for employees and their dependents. The coverage amount is up to ₹5 lakhs per family."
    },
    {
        "question": "How many holidays do we have?",
        "answer": "We observe 8 holidays per year including New Year's Day, Republic Day, Holi, Good Friday, Independence Day, Gandhi Jayanti, Diwali, and Christmas."
    },
    {
        "question": "What is the work from home policy?",
        "answer": "Employees can work from home twice a week with prior approval from their manager."
    },
    {
        "question": "How does the performance bonus work?",
        "answer": "Performance bonuses are awarded annually based on individual performance ratings and company performance. They are typically paid out in April."
    },
    {
        "question": "What is the probation period?",
        "answer": "The standard probation period is 3 months, which may be extended based on performance evaluation."
    },
    {
        "question": "How do I update my personal information?",
        "answer": "You can update your personal information through your employee profile in the dashboard. For major changes like bank details, please contact HR."
    }
]

def initialize_faq_database(mongo_db):
    """Initialize FAQ database with sample data"""
    # Check if FAQ collection exists and has data
    if mongo_db.hr_faq.count_documents({}) == 0:
        # Insert sample FAQ data
        mongo_db.hr_faq.insert_many(SAMPLE_FAQ)
        print("Initialized HR FAQ database with sample data")
    
    return True