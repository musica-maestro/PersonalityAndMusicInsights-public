import streamlit as st
import os
import sys
from datetime import datetime
import importlib.util
import time
import spotipy
from db_utils import get_mongo_client, generate_user_id

# Set page config - MUST be the first Streamlit command
st.set_page_config(
    page_title="Personality & Music Insights",
    page_icon="🎵",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Force light theme using custom CSS
def force_light_theme():
    st.markdown("""
    <style>
    /* Force light theme colors */
    .stApp {
        background-color: white !important;
        color: black !important;
    }
    
    /* Main content area */
    .main .block-container {
        background-color: white !important;
        color: black !important;
    }
    
    /* Sidebar */
    .css-1d391kg {
        background-color: #f0f2f6 !important;
    }
    
    /* Text elements */
    .stMarkdown, .stText, p, h1, h2, h3, h4, h5, h6 {
        color: black !important;
    }
    
    /* Buttons */
    .stButton > button {
        background-color: #ff4b4b !important;
        color: white !important;
        border: none !important;
    }
    
    .stButton > button:hover {
        background-color: #e03e3e !important;
        color: white !important;
    }
    
    /* Input fields */
    .stTextInput > div > div > input,
    .stSelectbox > div > div > select,
    .stTextArea > div > div > textarea {
        background-color: white !important;
        color: black !important;
        border: 1px solid #cccccc !important;
    }
    
    /* Progress bars */
    .stProgress > div > div > div {
        background-color: #ff4b4b !important;
    }
    
    /* Metrics */
    .metric-container {
        background-color: white !important;
        color: black !important;
    }
    
    /* Columns */
    .element-container {
        background-color: transparent !important;
    }
    
    /* Info/Warning/Error boxes */
    .stAlert {
        background-color: white !important;
        color: black !important;
        border: 1px solid #cccccc !important;
    }
    
    /* Tables */
    .stDataFrame {
        background-color: white !important;
        color: black !important;
    }
    
    /* Hide theme toggle if it exists */
    .stAppViewMain > div > div > div:nth-child(1) > div:nth-child(2) > div:nth-child(2) > div > div:nth-child(2) > div:nth-child(1) > div:nth-child(1) > div:nth-child(2) > div:nth-child(1) {
        display: none !important;
    }
    
    /* Additional selectors for theme toggle hiding */
    [data-testid="stToolbar"] {
        display: none !important;
    }
    
    /* Ensure all text is readable */
    * {
        color: black !important;
    }
    
    /* Exception for buttons and special elements that should have different colors */
    .stButton > button,
    .stButton > button *,
    .stProgress > div > div > div,
    .stProgress > div > div > div * {
        color: white !important;
    }
    </style>
    """, unsafe_allow_html=True)

# Apply the theme at the start of the app
force_light_theme()

# Import modules from files
def import_module_from_file(file_path, module_name):
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    if spec is None:
        st.error(f"Could not load module from {file_path}")
        return None
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module

# Initialize session states
if 'app_state' not in st.session_state:
    st.session_state.app_state = "welcome"  # Start with welcome page
if 'survey_completed' not in st.session_state:
    st.session_state.survey_completed = False
if 'demographics_completed' not in st.session_state:
    st.session_state.demographics_completed = False
if 'spotify_initialized' not in st.session_state:
    st.session_state.spotify_initialized = False
if 'spotify_data_collected' not in st.session_state:
    st.session_state.spotify_data_collected = False
if 'spotify_data_collection_attempted' not in st.session_state:
    st.session_state.spotify_data_collection_attempted = False
if 'spotify_auth_code' not in st.session_state:
    st.session_state.spotify_auth_code = None
if 'both_completed' not in st.session_state:
    st.session_state.both_completed = False

# Import our modules
welcome_module = import_module_from_file("welcome_page.py", "welcome")
survey_module = import_module_from_file("survey.py", "survey")
demographics_module = import_module_from_file("demographics.py", "demographics")
spotify_module = import_module_from_file("spotify.py", "spotify")
results_module = import_module_from_file("results_page.py", "results")

def welcome_page():
    # This is a wrapper to call our welcome page function
    welcome_module.welcome_page()

# Modify the on_survey_complete function in app.py
def on_survey_complete():
    st.session_state.survey_completed = True
    
    # Save survey results to MongoDB
    if 'score_results' in st.session_state:
        # Use responses_by_text if available, which stores questions as text keys
        if 'responses_by_text' in st.session_state:
            responses_data = st.session_state.responses_by_text
        else:
            # Fallback to original responses with numeric keys if text-based responses not available
            # Convert numeric keys to strings in responses dictionary
            responses_data = {str(key): value for key, value in st.session_state.responses.items()}
        
        # Create a combined object with both scores and individual responses
        survey_data = {
            "scores": st.session_state.score_results,
            "responses": responses_data
        }
        save_survey_results(survey_data)
    
    # Immediately redirect to Spotify page without showing intermediate message
    st.session_state.app_state = "results"
    st.rerun()

# Function to save survey results to MongoDB
def save_survey_results(survey_data):
    if 'mongo_connected' in st.session_state and st.session_state.mongo_connected:
        # Save to MongoDB using the updated function
        from db_utils import upsert_user_document  # Import from your new file
        upsert_user_document('big5', survey_data)
        st.session_state.survey_data_saved = True

# Function to handle demographics completion
def on_demographics_complete():
    st.session_state.demographics_completed = True
    st.session_state.app_state = "survey"
    st.rerun()  # Force a rerun to immediately show the survey

def survey_main():
    if hasattr(survey_module, 'main'):
        # Use a custom submit callback
        if 'submitted' in st.session_state and st.session_state.submitted:
            # If the survey is submitted, calculate scores and save them
            if 'responses' in st.session_state:
                score_results = survey_module.calculate_scores(st.session_state.responses)
                st.session_state.score_results = score_results
                
                # Instead of showing completion message, directly call on_survey_complete
                on_survey_complete()
        else:
            # Continue with the regular survey flow
            survey_module.main()
    
# Function to force refresh the page
def force_refresh():
    st.session_state.spotify_data_collection_attempted = False
    st.session_state.spotify_data_collected = False
    # st.rerun()

def init_spotify():
    status_placeholder = st.empty()
    
    if not st.session_state.spotify_initialized:
        status_placeholder.info("Waiting for Spotify connection...")
        
        # Initialize Spotify connection
        if hasattr(spotify_module, 'connect_to_spotify'):
            sp = spotify_module.connect_to_spotify()
            
            if sp:
                st.session_state.sp = sp
                st.session_state.spotify_initialized = True
                status_placeholder.success("Connected to Spotify!")
                
                # Start data collection
                collect_spotify_data(sp, status_placeholder)
    else:
        # If already initialized, check if data has been collected
        if not st.session_state.spotify_data_collected and not st.session_state.spotify_data_collection_attempted:
            if 'sp' in st.session_state:
                collect_spotify_data(st.session_state.sp, status_placeholder)
        elif st.session_state.spotify_data_collection_attempted and not st.session_state.spotify_data_collected:
            status_placeholder.warning("Previous data collection attempt failed. Please try again.")
            if st.button("Retry Data Collection"):
                st.session_state.spotify_data_collection_attempted = False
                st.rerun()

# Function to collect Spotify data
def collect_spotify_data(sp, status_placeholder):
    st.session_state.spotify_data_collection_attempted = True
    
    if hasattr(spotify_module, 'fetch_and_save_all_data'):
        with st.spinner("Collecting your Spotify data..."):
            status_placeholder.info("Fetching your Spotify data... This may take a moment.")
            try:
                success = spotify_module.fetch_and_save_all_data(sp)
                if success:
                    st.session_state.spotify_data_collected = True
                    status_placeholder.success("Successfully collected your Spotify data!")
                    st.session_state.app_state = "demographics"
                    st.rerun()
                    # Check if both components are completed
                    if st.session_state.survey_completed:
                        st.session_state.both_completed = True
                        st.session_state.app_state = "demographics"
                        st.rerun()
            except Exception as e:
                status_placeholder.error(f"Error collecting Spotify data: {e}")
                st.code(str(e), language="python")  # Show detailed error
                if st.button("Retry Data Collection"):
                    st.session_state.spotify_data_collection_attempted = False
                    st.session_state.spotify_data_collected = False
                    st.rerun()

# Main app flow
def main():
    # Apply theme on every rerun to ensure it persists
    force_light_theme()

    query_params = st.query_params
    
    # Check if this is a Spotify callback
    if 'code' in query_params:
        # We've received the authorization code from Spotify
        auth_code = query_params['code']
        
        # Store the code in session state
        st.session_state.spotify_auth_code = auth_code
        
        # Initialize Spotify with the code
        if 'spotify_initialized' not in st.session_state or not st.session_state.spotify_initialized:
            sp_oauth = spotify_module.get_spotify_oauth()
            try:
                token_info = sp_oauth.get_access_token(auth_code)
                if token_info:
                    sp = spotipy.Spotify(auth=token_info['access_token'])
                    st.session_state.sp = sp
                    st.session_state.spotify_initialized = True
                    st.session_state.app_state = "spotify"  # Move to the Spotify data page
                    
                    # Clear the code from the URL to prevent reusing it
                    st.query_params.clear()
                    
                    # Start data collection
                    collect_spotify_data(sp, st.empty())
            except Exception as e:
                st.error(f"Error with Spotify authorization: {e}")
        
        # Rerun the app without the query parameters
        st.rerun()
    
    # Initialize MongoDB connection automatically
    if 'mongo_connected' not in st.session_state:
        try:
            client = get_mongo_client()
            if client:
                st.session_state.mongo_client = client
                st.session_state.mongo_db = client['PersonalityAndMusic']
                st.session_state.mongo_connected = True
                
                # Generate unique user ID
                generate_user_id()
            else:
                st.session_state.mongo_connected = False
        except Exception as e:
            st.session_state.mongo_connected = False
    
    # Progress bar and step indicator
    steps = {"welcome": 1, "demographics": 2, "survey": 3, "spotify": 4, "results": 5}
    current_step = steps.get(st.session_state.app_state, 1)
    total_steps = 5
    
    # Main app state management
    if st.session_state.app_state == "welcome":
        welcome_page()
    elif st.session_state.app_state == "spotify":
        st.title("Your Spotify Music Profile")
        st.markdown("Connect your Spotify account to analyze your music preferences.")
        
        if not st.session_state.spotify_initialized or not st.session_state.spotify_data_collected:
            init_spotify()
        else:
            # If data is collected, show a button to move to results
            st.info("Your Spotify data has been successfully collected!")
            
            # Since survey must be completed before reaching this point,
            # only show the option to view results
            if st.button("View Your Complete Results"):
                st.session_state.app_state = "demographics"
                st.rerun()
    elif st.session_state.app_state == "demographics":
        if demographics_module.main():  # This returns True when demographics are completed
            on_demographics_complete()
    elif st.session_state.app_state == "survey":
        if not st.session_state.survey_completed:
            survey_main()
        else:
            st.session_state.app_state = "spotify"
            st.rerun()
    elif st.session_state.app_state == "results":
        # Check if both components are completed
        if st.session_state.survey_completed and st.session_state.spotify_data_collected:
            # Call the integrated results page
            results_module.main()
        else:
            if not st.session_state.survey_completed:
                st.warning("Il survey non risulta completed (?)")
            if not st.session_state.spotify_data_collected:
                st.warning("La collection di dati di spotify non risulta fatta (?)")
            st.warning("Please complete both the personality survey and Spotify data collection to view your complete results.")
            
            # Provide buttons to complete missing components
            if not st.session_state.survey_completed:
                if st.button("Complete Personality Survey"):
                    st.session_state.app_state = "survey"
                    st.rerun()
            
            if not st.session_state.spotify_data_collected:
                if st.button("Connect to Spotify"):
                    st.session_state.app_state = "spotify"
                    st.rerun()

if __name__ == "__main__":
    main()