import os
import redis
from werkzeug.security import generate_password_hash, check_password_hash
import json

# Global variable to hold the Redis client instance.
_redis_client = None

def get_redis_client():
    """
    Initializes and returns a singleton Redis client instance.
    This connects directly to the Vercel KV (Redis) database using the connection string.
    """
    global _redis_client
    if _redis_client is None:
        # Get the connection URL from environment variables
        redis_url = os.environ.get('KV_URL')
        if not redis_url:
            # This will happen locally if KV_URL is not in a .env file.
            # The app will show an error but not crash.
            raise ConnectionError("KV_URL environment variable not set. Cannot connect to Redis.")
        
        # Create a Redis client from the URL
        _redis_client = redis.from_url(redis_url)
    return _redis_client

# Define the special user's email
SPECIAL_USER_EMAIL = "cn8964@8964.com"
DEFAULT_ANALYSIS_CREDITS = 10

def get_user(email):
    """Fetches a user from Redis by email."""
    try:
        r = get_redis_client()
        user_data = r.get(f"user:{email}")
        if user_data:
            return json.loads(user_data)
        return None
    except redis.exceptions.RedisError as e:
        print(f"Redis error in get_user: {e}")
        return None

def create_user(email, password):
    """Creates a new user in Redis."""
    try:
        r = get_redis_client()
        hashed_password = generate_password_hash(password)
        user_data = {
            "email": email,
            "password": hashed_password,
            "analysis_credits": DEFAULT_ANALYSIS_CREDITS
        }
        # Use SET with NX=True to only set if the key does not already exist.
        # This makes the operation atomic and prevents race conditions.
        if r.set(f"user:{email}", json.dumps(user_data), nx=True):
            return user_data
        else:
            return None # User already exists
    except redis.exceptions.RedisError as e:
        print(f"Redis error in create_user: {e}")
        return None

def verify_user(email, password):
    """Verifies a user's password."""
    user = get_user(email)
    if user and check_password_hash(user['password'], password):
        return user
    return None

def get_credits(email):
    """Gets the analysis credits for a user."""
    if email == SPECIAL_USER_EMAIL:
        return float('inf')  # Special user has infinite credits
    user = get_user(email)
    return user['analysis_credits'] if user else 0

def use_credit(email):
    """Decrements a user's analysis credits by one."""
    if email == SPECIAL_USER_EMAIL:
        return True  # Special user does not lose credits
    
    try:
        r = get_redis_client()
        user_key = f"user:{email}"
        
        # Use a transaction to safely read, check, and decrement credits
        with r.pipeline() as pipe:
            while True:
                try:
                    pipe.watch(user_key)
                    user_data_str = pipe.get(user_key)
                    if not user_data_str:
                        pipe.unwatch()
                        return False # User not found
                    
                    user_data = json.loads(user_data_str)
                    
                    if user_data['analysis_credits'] <= 0:
                        pipe.unwatch()
                        return False # No credits left
                    
                    user_data['analysis_credits'] -= 1
                    
                    pipe.multi()
                    pipe.set(user_key, json.dumps(user_data))
                    pipe.execute()
                    return True
                except redis.exceptions.WatchError:
                    # The key was modified by another client, retry the transaction
                    continue
    except redis.exceptions.RedisError as e:
        print(f"Redis error in use_credit: {e}")
        return False

def initialize_special_user():
    """Ensures the special user exists in the database."""
    try:
        r = get_redis_client()
        user_key = f"user:{SPECIAL_USER_EMAIL}"
        if not r.exists(user_key):
            create_user(SPECIAL_USER_EMAIL, os.environ.get("SPECIAL_USER_PASSWORD", "cn8964"))
            print(f"Special user {SPECIAL_USER_EMAIL} initialized.")
    except ConnectionError as e:
         print(f"WARNING: Could not initialize special user. This is expected if running locally without Vercel KV environment variables. Error: {e}")
    except redis.exceptions.RedisError as e:
        print(f"Redis error during special user initialization: {e}") 