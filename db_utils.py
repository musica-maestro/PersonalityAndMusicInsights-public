#Modified MongoDB integration for unified schema
import streamlit as st
from pymongo import MongoClient
from datetime import datetime
import time
import uuid

def retry_connection(max_attempts=3, delay=2):
    """
    Decorator to retry MongoDB operations
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            attempts = 0
            while attempts < max_attempts:
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    attempts += 1
                    if attempts == max_attempts:
                        st.error(f"Failed after {max_attempts} attempts: {e}")
                        return None
                    st.warning(f"Connection attempt {attempts} failed, retrying in {delay} seconds...")
                    time.sleep(delay)
        return wrapper
    return decorator

def get_mongo_client():
    """
    Create and return a MongoDB client using connection string from secrets
    """
    try:
        mongo_uri = st.secrets["mongo_uri"]
        client = MongoClient(mongo_uri, serverSelectionTimeoutMS=5000)
        # Test the connection
        client.admin.command('ping')
        return client
    except Exception as e:
        st.error(f"Failed to connect to MongoDB: {e}")
        return None

def generate_user_id():
    """
    Generate a unique user ID if one doesn't exist
    """
    if 'user_id' not in st.session_state:
        st.session_state.user_id = str(uuid.uuid4())
    return st.session_state.user_id

@retry_connection(max_attempts=3)
def upsert_user_document(data_type, data):
    """
    Update a specific section of the user document based on data_type
    This follows the unified structure with a single document per user
    
    Args:
        data_type: Type of data being saved (demografica, big5, spotify)
        data: Dictionary of data to save in this section
    """
    if 'mongo_connected' not in st.session_state or not st.session_state.mongo_connected:
        st.warning("Not connected to MongoDB. Attempting to reconnect...")
        try:
            client = get_mongo_client()
            if client:
                st.session_state.mongo_client = client
                st.session_state.mongo_db = client['PersonalityAndMusic']
                st.session_state.mongo_connected = True
            else:
                return False
        except Exception:
            return False
    
    try:
        # Generate or get user ID
        user_id = generate_user_id()
        
        # Use a single 'users' collection instead of per-user collections
        collection = st.session_state.mongo_db['users']
        
        # Current timestamp
        now = datetime.now()
        
        # Document structure with unified schema
        update_field = {}
        #update_field2 = {}
        
        # Map the data_type to our unified schema field names
        field_mapping = {
            'survey_results': 'big5',
            'top_tracks_short_term': 'spotify',
            'top_tracks_long_term': 'spotify',
            'top_tracks_medium_term': 'spotify',
            'top_artists_short_term': 'spotify',
            'top_artists_medium_term': 'spotify',
            'top_artists_long_term': 'spotify',
            'recently_played': 'spotify',
            'playlists': 'spotify',
            'following': 'spotify'
        }
        
        field_name = field_mapping.get(data_type, data_type)
        
        # For spotify data, we need to handle multiple sub-types
        if field_name == 'spotify':
            update_field = {f"{field_name}.{data_type}": data}
            #update_field2 = {{field_name}: update_field1}
        else:
            update_field = {field_name: data}
        
        # Create or update document
        result = collection.update_one(
            {"id": user_id},
            {
                "$set": {
                    **update_field,
                    #"modified_at": now
                },
                "$setOnInsert": {
                    "id": user_id,
                    "created_at": now
                }
            },
            upsert=True
        )
        
        return True
    except Exception as e:
        st.error(f"MongoDB save error: {e}")
        return False

def get_user_data(user_id=None):
    """
    Retrieve the complete user document
    
    Args:
        user_id: Optional user ID (defaults to current user)
        
    Returns:
        Complete user document or None if not found
    """
    if 'mongo_connected' not in st.session_state or not st.session_state.mongo_connected:
        st.warning("Not connected to MongoDB. Cannot retrieve data.")
        return None
    
    if user_id is None:
        user_id = generate_user_id()
    
    try:
        collection = st.session_state.mongo_db['users']
        return collection.find_one({"id": user_id})
    except Exception as e:
        st.error(f"Error retrieving data: {e}")
        return None