import os
from vercel_kv import KV
from werkzeug.security import generate_password_hash, check_password_hash
import json

# Instantiate the KV client
kv = KV()

# Define the special user's email
SPECIAL_USER_EMAIL = "cn8964@8964.com"
DEFAULT_ANALYSIS_CREDITS = 10

def get_user(email):
    """Fetches a user's data from Vercel KV by email."""
    user_data_json = kv.get(f"user:{email}")
    if user_data_json:
        return json.loads(user_data_json)
    return None

def create_user(username, email, password):
    """Creates a new user in Vercel KV."""
    if get_user(email):
        return None  # User already exists

    hashed_password = generate_password_hash(password)
    
    # Special user gets unlimited credits
    if email == SPECIAL_USER_EMAIL:
        credits = float('inf')
    else:
        credits = DEFAULT_ANALYSIS_CREDITS

    user_data = {
        'username': username,
        'email': email,
        'password_hash': hashed_password,
        'analysis_credits': credits
    }
    kv.set(f"user:{email}", json.dumps(user_data))
    return user_data

def check_password(user_password_hash, password):
    """Checks if the provided password matches the stored hash."""
    return check_password_hash(user_password_hash, password)

def get_remaining_credits(email):
    """Gets the remaining analysis credits for a user."""
    user_data = get_user(email)
    if not user_data:
        return 0
    
    if user_data.get('analysis_credits') == float('inf'):
        return "unlimited"
        
    return user_data.get('analysis_credits', 0)

def use_credit(email):
    """Decrements the analysis credit for a user."""
    # Special user has unlimited credits, so no need to decrement
    if email == SPECIAL_USER_EMAIL:
        return True

    user_data = get_user(email)
    if not user_data:
        return False # Should not happen for a logged-in user

    current_credits = user_data.get('analysis_credits', 0)
    
    if current_credits > 0:
        user_data['analysis_credits'] = current_credits - 1
        kv.set(f"user:{email}", json.dumps(user_data))
        return True
    
    return False

# You can add a function here to pre-register the special user if needed
# For example, to be run from a separate script or the first time the app starts
def initialize_special_user():
    """Ensures the special user exists in the database."""
    if not get_user(SPECIAL_USER_EMAIL):
        print(f"Creating special user: {SPECIAL_USER_EMAIL}")
        # The password for the special user is 'cn8964' as per previous context
        create_user(
            username="Admin",
            email=SPECIAL_USER_EMAIL,
            password="cn8964" # This should be a securely handled password
        )

# When this module is imported, we can ensure the special user is created.
# However, running this on every import in a serverless function can be inefficient.
# It's better to run initialization as a separate step during deployment.
# For simplicity in this context, we will call it once.
# A better approach for production would be a CLI command `flask init-db`.
# initialize_special_user() 