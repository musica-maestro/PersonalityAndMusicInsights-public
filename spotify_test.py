"""
Simple test script to verify Spotify connectivity and data display.
Run this directly to test Spotify functionality without the full app workflow.
"""
import streamlit as st
import sys
import importlib.util

# Set page config
st.set_page_config(
    page_title="Spotify Test",
    page_icon="🎵",
    layout="wide"
)

# Import Spotify module
def import_module_from_file(file_path, module_name):
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    if spec is None:
        st.error(f"Could not load module from {file_path}")
        return None
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module

# Initialize session state if needed
if 'sp' not in st.session_state:
    st.session_state.sp = None

# Import Spotify module
spotify_module = import_module_from_file("spotify.py", "spotify")

st.title("Spotify Connection Test")
st.write("This is a test app to verify your Spotify connection works correctly.")

# Connect to Spotify button
if st.button("Connect to Spotify") or st.session_state.sp is None:
    if hasattr(spotify_module, 'connect_to_spotify'):
        with st.spinner("Connecting to Spotify..."):
            sp = spotify_module.connect_to_spotify()
            if sp:
                st.session_state.sp = sp
                st.success("Successfully connected to Spotify!")
            else:
                st.error("Failed to connect to Spotify.")
                
                # If connection failed, show manual code entry
                st.subheader("Manual Authorization")
                st.write("If you were redirected to a URL, copy the code parameter from that URL.")
                auth_code = st.text_input("Enter the authorization code:")
                
                if auth_code and st.button("Submit Code"):
                    try:
                        sp_oauth = spotify_module.get_spotify_oauth()
                        token_info = sp_oauth.get_access_token(auth_code)
                        if token_info:
                            import spotipy
                            sp = spotipy.Spotify(auth=token_info['access_token'])
                            st.session_state.sp = sp
                            st.success("Successfully connected with authorization code!")
                    except Exception as e:
                        st.error(f"Error with authorization code: {e}")

# If successfully connected, show the main Spotify interface
if 'sp' in st.session_state and st.session_state.sp:
    st.subheader("Spotify Connection Status")
    st.write("✅ Connected to Spotify")
    
    # Test displaying user profile
    try:
        profile = st.session_state.sp.current_user()
        st.subheader(f"Welcome, {profile['display_name']}!")
        
        if profile['images'] and len(profile['images']) > 0:
            st.image(profile['images'][0]['url'], width=200)
        
        st.write(f"Account type: {profile.get('product', 'Unknown').capitalize()}")
    except Exception as e:
        st.error(f"Error loading profile: {e}")
    
    # Add button to show the full Spotify interface
    if st.button("Show Full Spotify Interface"):
        if hasattr(spotify_module, 'main'):
            try:
                spotify_module.main()
            except Exception as e:
                st.error(f"Error displaying Spotify interface: {e}")
                st.code(str(e), language="python")