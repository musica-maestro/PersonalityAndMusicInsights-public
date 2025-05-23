# Updated spotify.py with browser-based token management
import streamlit as st
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import pandas as pd
import time
from datetime import datetime, timedelta
import pytz
import json
import base64
from urllib.parse import parse_qs, urlparse

# Spotify API credentials
CLIENT_ID = st.secrets["spotify"]["client_id"]
CLIENT_SECRET = st.secrets["spotify"]["client_secret"]
REDIRECT_URI = st.secrets["spotify"]["redirect_uri"]
SCOPE = "user-read-private user-read-email user-top-read user-follow-read playlist-read-private user-read-recently-played"

class StreamlitSpotifyAuth:
    def __init__(self):
        self.client_id = CLIENT_ID
        self.client_secret = CLIENT_SECRET
        self.redirect_uri = REDIRECT_URI
        self.scope = SCOPE
        self.sp_oauth = SpotifyOAuth(
            client_id=self.client_id,
            client_secret=self.client_secret,
            redirect_uri=self.redirect_uri,
            scope=self.scope,
            cache_path=".cache",  # Use a cache path - will be managed by session state
            show_dialog=True      # MODIFIED: Ensures login/auth dialog is always shown
        )
    
    def get_token_from_session(self):
        """Get token from Streamlit session state"""
        if 'spotify_token' in st.session_state:
            token_info = st.session_state.spotify_token
            
            # Check if token needs refresh
            if self.is_token_expired(token_info):
                return self.refresh_token(token_info)
            
            return token_info
        return None
    
    def save_token_to_session(self, token_info):
        """Save token to Streamlit session state"""
        st.session_state.spotify_token = token_info
    
    def is_token_expired(self, token_info):
        """Check if token is expired"""
        if not token_info:
            return True
        
        expires_at = token_info.get('expires_at', 0)
        return time.time() > expires_at
    
    def refresh_token(self, token_info):
        """Refresh the access token"""
        try:
            if 'refresh_token' in token_info:
                new_token = self.sp_oauth.refresh_access_token(token_info['refresh_token'])
                self.save_token_to_session(new_token)
                return new_token
        except Exception as e:
            st.error(f"Error refreshing token: {e}")
            # Clear invalid token
            if 'spotify_token' in st.session_state:
                del st.session_state.spotify_token
        return None
    
    def get_auth_url(self):
        """Get authorization URL"""
        # show_dialog=True in __init__ means this URL will always prompt
        return self.sp_oauth.get_authorize_url() 
    
    def get_token_from_code(self, code):
        """Exchange authorization code for token"""
        try:
            token_info = self.sp_oauth.get_access_token(code, check_cache=False) # check_cache=False as we manage cache via session
            self.save_token_to_session(token_info)
            return token_info
        except Exception as e:
            st.error(f"Error getting token from code: {e}")
            return None

def get_spotify_oauth():
    """Function to get SpotifyOAuth instance"""
    return SpotifyOAuth(
        client_id=CLIENT_ID,
        client_secret=CLIENT_SECRET,
        redirect_uri=REDIRECT_URI,
        scope=SCOPE,
        cache_path=".cache",  # Use a cache path - will be ignored in our implementation
        show_dialog=True      # MODIFIED: Ensures login/auth dialog is always shown
    )

def get_spotify_client():
    """Get authenticated Spotify client"""
    return connect_to_spotify()

# Alternative approach using URL parameters for token handling
def handle_callback():
    """Handle OAuth callback from URL parameters"""
    query_params = st.query_params
    
    if 'code' in query_params:
        code = query_params['code']
        auth = StreamlitSpotifyAuth()
        token_info = auth.get_token_from_code(code)
        
        if token_info:
            st.success("Successfully authenticated with Spotify!")
            # Clear URL parameters
            st.query_params.clear()
            st.rerun() # Rerun to update the UI state
        else:
            st.error("Failed to authenticate with Spotify.")
            # Clear potentially problematic code from URL to avoid re-processing
            st.query_params.clear() 
            st.rerun()
    
    elif 'error' in query_params:
        error = query_params['error']
        st.error(f"Spotify authentication error: {error}")
        st.query_params.clear() # Clear error from URL
        st.rerun()


def connect_to_spotify():
    """Connect to Spotify using browser-based auth"""
    try:
        # Handle OAuth callback first if code or error in URL params
        if 'code' in st.query_params or 'error' in st.query_params:
            handle_callback() # This function will rerun if it processes a code/error
            # If handle_callback reruns, the rest of this function won't execute in this pass
            # If it doesn't find a code/error to process, it will continue
        
        auth = StreamlitSpotifyAuth()
        token_info = auth.get_token_from_session()
        
        if not token_info:
            st.markdown("### Connect to Spotify")
            st.write("Please click the button below to authorize this app to access your Spotify data:")
            
            auth_url = auth.get_auth_url()
            
            # Create a more prominent button
            st.markdown(f"""
            <div style="text-align: center; margin: 20px 0;">
                <a href="{auth_url}" target="_self" style="text-decoration: none;">
                    <button style="
                        background-color: #1DB954; 
                        color: white; 
                        padding: 15px 30px; 
                        border: none; 
                        border-radius: 50px; 
                        font-weight: bold; 
                        font-size: 16px;
                        cursor: pointer;
                        box-shadow: 0 4px 8px rgba(0,0,0,0.1);
                        transition: all 0.3s ease;
                    " onmouseover="this.style.backgroundColor='#1ed760'" 
                       onmouseout="this.style.backgroundColor='#1DB954'">
                        🎵 Connect to Spotify
                    </button>
                </a>
            </div>
            """, unsafe_allow_html=True)
            
            st.info("You'll be redirected to Spotify to log in and authorize, then back to this app.")
            return None # Important to return None to stop further execution until authenticated
        
        # Create Spotify client with valid token
        return spotipy.Spotify(auth=token_info['access_token'])
    
    except Exception as e:
        st.error(f"Error connecting to Spotify: {e}")
        # Potentially clear token if it's causing issues
        # if 'spotify_token' in st.session_state:
        #     del st.session_state.spotify_token
        return None

# Alternative: Using browser localStorage (requires JavaScript)
# This part is for client-side persistence if desired, but current auth flow focuses on session_state
def setup_browser_storage():
    """Setup browser localStorage for token storage"""
    st.markdown("""
    <script>
    // Function to save token to localStorage
    function saveSpotifyToken(token) {
        localStorage.setItem('spotify_token', JSON.stringify(token));
    }
    
    // Function to get token from localStorage
    function getSpotifyToken() {
        const token = localStorage.getItem('spotify_token');
        return token ? JSON.parse(token) : null;
    }
    
    // Function to clear token from localStorage
    function clearSpotifyToken() {
        localStorage.removeItem('spotify_token');
    }
    
    // Make functions globally available
    window.spotifyAuth = {
        saveToken: saveSpotifyToken,
        getToken: getSpotifyToken,
        clearToken: clearSpotifyToken
    };
    </script>
    """, unsafe_allow_html=True)

# Function to logout/clear token
def logout_spotify():
    """Clear Spotify authentication from session state"""
    if 'spotify_token' in st.session_state:
        del st.session_state.spotify_token
    # Optionally, clear localStorage if it's being used
    # st.markdown("<script>window.spotifyAuth.clearToken();</script>", unsafe_allow_html=True)
    st.success("Successfully logged out from Spotify!")
    st.rerun()

# Main app function with logout option
def main():
    st.set_page_config(page_title="Spotify Dashboard", layout="wide")
    # Setup browser storage (optional, not directly used by Python auth logic here)
    # setup_browser_storage() # Uncomment if you plan to use localStorage sync
    
    # Add logout button in sidebar if authenticated
    # Check for token before attempting to create the button
    # This avoids trying to access session_state too early or unnecessarily
    # The connect_to_spotify function will handle the display of login UI if not authenticated
    
    sp = connect_to_spotify() # This handles auth and returns client or None

    if sp:
        if 'spotify_token' in st.session_state: # Ensure token exists before showing logout
            st.sidebar.markdown("---")
            if st.sidebar.button("🚪 Logout from Spotify", type="secondary"):
                logout_spotify() # This will rerun the app

        try:
            # Test the connection and get user info
            user = sp.current_user()
            st.success(f"Successfully connected to Spotify! Welcome, {user['display_name']}!")
            
            # Store user info in session
            st.session_state.spotify_user = user
            
            # Create sidebar with options
            st.sidebar.title("Navigation")
            selection = st.sidebar.radio(
                "Information",
                ["Top Tracks", "Top Artists", "Recently Played"] # Add other options as needed
            )
            
            # Display selected content
            if selection == "Top Tracks":
                display_top_tracks(sp)
            elif selection == "Top Artists":
                display_top_artists(sp)
            elif selection == "Recently Played":
                display_recently_played(sp)
            # Add other sections like:
            # elif selection == "Playlists":
            #     display_playlists(sp)
            # elif selection == "Followed Artists":
            #     display_following(sp)

            # Example: Button to fetch and save all data to DB
            # This might be better placed elsewhere or triggered differently
            # if st.sidebar.button("Sync Data to DB"):
            #     with st.spinner("Fetching and saving all Spotify data..."):
            #         if fetch_and_save_all_data(sp):
            #             st.sidebar.success("Data synced successfully!")
            #         else:
            #             st.sidebar.error("Failed to sync data.")
                
        except spotipy.exceptions.SpotifyException as e:
            st.error(f"Spotify API error: {e}")
            if "token expired" in str(e).lower() or e.http_status == 401:
                st.info("Your session has expired or is invalid. Please log out and reconnect.")
                # Automatically clear the potentially bad token
                if 'spotify_token' in st.session_state:
                    del st.session_state.spotify_token
                if st.button("Reconnect to Spotify"):
                    st.rerun() # Will trigger the login flow again
            # else:
            # The logout button is always available if sp is not None
            # if st.button("Logout and try again"):
            # logout_spotify()
        except Exception as e:
            st.error(f"An unexpected error occurred: {e}")
            # if st.button("Logout and try again"):
            # logout_spotify()
    # else:
        # If sp is None, connect_to_spotify() has already displayed the login button
        # or an error message. No further action needed here for the main content area.
        # The sidebar for logout shouldn't appear if sp is None.
        pass


# Enhanced token validation
def validate_spotify_connection(sp):
    """Validate if Spotify connection is still valid"""
    if not sp: return False
    try:
        sp.current_user() # A simple API call to check validity
        return True
    except spotipy.exceptions.SpotifyException as e:
        # Specifically check for auth errors
        if e.http_status == 401 or e.http_status == 403: 
            return False
        # For other Spotify errors, we might still consider the connection "valid" but API call failed
        # However, for simplicity here, any SpotifyException means connection is problematic for current use.
        return False 
    except Exception: # Other network errors etc.
        return False

# Token refresh mechanism
def ensure_valid_token(sp_instance):
    """Ensure token is valid, attempt refresh if needed. Returns a new sp_instance or None."""
    if validate_spotify_connection(sp_instance):
        return sp_instance

    # If validation fails, try to refresh
    auth_manager = StreamlitSpotifyAuth() # Re-create to access refresh logic
    token_info = auth_manager.get_token_from_session() # Get current token from session

    if token_info and 'refresh_token' in token_info:
        st.info("Spotify token may have expired. Attempting to refresh...")
        new_token_info = auth_manager.refresh_token(token_info)
        if new_token_info:
            st.success("Token refreshed successfully!")
            return spotipy.Spotify(auth=new_token_info['access_token'])
        else:
            st.error("Failed to refresh token. Please log out and log in again.")
            # Clear the invalid token from session to force re-authentication
            if 'spotify_token' in st.session_state:
                del st.session_state.spotify_token
            st.button("Login to Spotify", on_click=lambda: st.rerun()) # Offer a button to re-trigger login
            return None
    else:
        # No refresh token or no token at all, force re-login
        st.warning("Spotify authentication is invalid or missing. Please log in.")
        if 'spotify_token' in st.session_state:
            del st.session_state.spotify_token # Clear any partial/invalid token
        st.button("Login to Spotify", on_click=lambda: st.rerun())
        return None


# Your existing display functions remain the same...
def display_top_tracks(sp):
    st.header("Your Top Tracks")
    
    time_range = st.radio(
        "Time Range",
        ["short_term", "medium_term", "long_term"],
        format_func=lambda x: {
            "short_term": "Last 4 Weeks",
            "medium_term": "Last 6 Months", 
            "long_term": "All Time"
        }[x],
        key="top_tracks_time_range" # Unique key for radio
    )
    
    sp = ensure_valid_token(sp) # Ensure token is valid before API call
    if not sp:
        # ensure_valid_token already shows messages and potentially a reconnect button
        return 
    
    try:
        top_tracks = sp.current_user_top_tracks(limit=21, time_range=time_range) # e.g. 21 for 3 columns
    except spotipy.exceptions.SpotifyException as e:
        st.error(f"Could not load top tracks: {e}")
        if e.http_status == 401: # Unauthorized
            if 'spotify_token' in st.session_state: del st.session_state.spotify_token
            st.button("Reconnect to Spotify", on_click=lambda: st.rerun())
        return
    
    if not top_tracks['items']:
        st.info("No top tracks found for this time period.")
        return
    
    tracks_data = []
    for i, track in enumerate(top_tracks['items'], 1):
        artists = ", ".join([artist['name'] for artist in track['artists']])
        album = track['album']['name']
        preview_url = track['preview_url']
        track_url = track['external_urls']['spotify']
        image_url = track['album']['images'][0]['url'] if track['album']['images'] else "https://via.placeholder.com/150" # Placeholder
        
        tracks_data.append({
            "Rank": i, "Track": track['name'], "Artist(s)": artists, "Album": album,
            "Preview": preview_url, "Spotify Link": track_url, "Image": image_url,
            "track_id": track['id'], "time_range": time_range
        })
    
    cols = st.columns(3)
    for i, item in enumerate(tracks_data):
        with cols[i % 3]:
            if item['Image']: st.image(item['Image'], width=150)
            st.write(f"**{i+1}. {item['Track']}**")
            st.write(f"_{item['Artist(s)']}_")
            st.caption(f"Album: {item['Album']}")
            if item['Preview']: st.audio(item['Preview'], format="audio/mp3", start_time=0)
            st.markdown(f"[Open on Spotify]({item['Spotify Link']})", unsafe_allow_html=True)
            st.markdown("---")

def display_top_artists(sp):
    st.header("Your Top Artists")
    
    time_range = st.radio(
        "Time Range",
        ["short_term", "medium_term", "long_term"],
        format_func=lambda x: {
            "short_term": "Last 4 Weeks",
            "medium_term": "Last 6 Months", 
            "long_term": "All Time"
        }[x],
        key="top_artists_time_range" # Unique key
    )

    sp = ensure_valid_token(sp)
    if not sp: return

    try:
        top_artists = sp.current_user_top_artists(limit=21, time_range=time_range)
    except spotipy.exceptions.SpotifyException as e:
        st.error(f"Could not load top artists: {e}")
        if e.http_status == 401:
            if 'spotify_token' in st.session_state: del st.session_state.spotify_token
            st.button("Reconnect to Spotify", on_click=lambda: st.rerun())
        return
    
    if not top_artists['items']:
        st.info("No top artists found for this time period.")
        return
    
    artists_data = []
    for i, artist in enumerate(top_artists['items'], 1):
        genres = ", ".join(artist['genres'][:3]) if artist['genres'] else "N/A" # Show top 3 genres
        image_url = artist['images'][0]['url'] if artist['images'] else "https://via.placeholder.com/150"
        
        artists_data.append({
            "Rank": i, "Artist": artist['name'], "Genres": genres,
            "Popularity": artist['popularity'], "Followers": artist['followers']['total'],
            "Spotify Link": artist['external_urls']['spotify'], "Image": image_url,
            "artist_id": artist['id'], "time_range": time_range
        })
    
    cols = st.columns(3)
    for i, item in enumerate(artists_data):
        with cols[i % 3]:
            if item['Image']: st.image(item['Image'], width=150)
            st.write(f"**{i+1}. {item['Artist']}**")
            st.caption(f"Genres: {item['Genres']}")
            st.write(f"Popularity: {item['Popularity']}/100")
            st.write(f"Followers: {item['Followers']:,}")
            st.markdown(f"[Open on Spotify]({item['Spotify Link']})", unsafe_allow_html=True)
            st.markdown("---")


def display_recently_played(sp):
    st.header("Your Recently Played Tracks")

    sp = ensure_valid_token(sp)
    if not sp: return

    try:
        results = sp.current_user_recently_played(limit=21)
    except spotipy.exceptions.SpotifyException as e:
        st.error(f"Could not load recently played tracks: {e}")
        if e.http_status == 401:
            if 'spotify_token' in st.session_state: del st.session_state.spotify_token
            st.button("Reconnect to Spotify", on_click=lambda: st.rerun())
        return
    
    if not results['items']:
        st.info("No recently played tracks found.")
        return
    
    tracks_data = []
    unique_tracks = {} # To avoid showing same track multiple times if played consecutively
    for item in results['items']:
        track = item['track']
        if track['id'] not in unique_tracks: # Simple de-duplication for display
            unique_tracks[track['id']] = item 
    
    processed_items = list(unique_tracks.values())[:21] # Limit after de-duplication

    for i, item in enumerate(processed_items, 1):
        track = item['track']
        played_at_str = item['played_at']
        
        utc_time = datetime.strptime(played_at_str, '%Y-%m-%dT%H:%M:%S.%fZ').replace(tzinfo=pytz.utc)
        rome_tz = pytz.timezone('Europe/Rome')
        rome_time = utc_time.astimezone(rome_tz)
        
        # Calculate "time ago"
        now_rome = datetime.now(rome_tz)
        time_diff = now_rome - rome_time
        
        if time_diff < timedelta(minutes=1): time_ago = "Just now"
        elif time_diff < timedelta(hours=1): time_ago = f"{int(time_diff.total_seconds() / 60)} min ago"
        elif time_diff < timedelta(days=1): time_ago = f"{int(time_diff.total_seconds() / 3600)} hr ago"
        else: time_ago = f"{time_diff.days} day(s) ago"

        artists = ", ".join([artist['name'] for artist in track['artists']])
        album = track['album']['name']
        preview_url = track['preview_url']
        track_url = track['external_urls']['spotify']
        image_url = track['album']['images'][0]['url'] if track['album']['images'] else "https://via.placeholder.com/150"
        
        tracks_data.append({
            "Track": track['name'], "Artist(s)": artists, "Album": album,
            "Played At": rome_time.strftime('%Y-%m-%d %H:%M:%S'), "Time Ago": time_ago,
            "Preview": preview_url, "Spotify Link": track_url, "Image": image_url
        })
    
    cols = st.columns(3)
    for i, item in enumerate(tracks_data):
        with cols[i % 3]:
            if item['Image']: st.image(item['Image'], width=150)
            st.write(f"**{item['Track']}**")
            st.write(f"_{item['Artist(s)']}_")
            st.caption(f"Album: {item['Album']}")
            st.caption(f"Played: {item['Time Ago']} ({item['Played At']})")
            if item['Preview']: st.audio(item['Preview'], format="audio/mp3", start_time=0)
            st.markdown(f"[Open on Spotify]({item['Spotify Link']})", unsafe_allow_html=True)
            st.markdown("---")
    
    with st.expander("View as table (raw recently played)"):
        df_raw_recent = []
        for item in results['items']: # Use original results for table
            track = item['track']
            played_at_str = item['played_at']
            utc_time = datetime.strptime(played_at_str, '%Y-%m-%dT%H:%M:%S.%fZ').replace(tzinfo=pytz.utc)
            rome_tz = pytz.timezone('Europe/Rome')
            rome_time = utc_time.astimezone(rome_tz)
            df_raw_recent.append({
                "Track": track['name'], 
                "Artist(s)": ", ".join([a['name'] for a in track['artists']]),
                "Played At (Local)": rome_time.strftime('%Y-%m-%d %H:%M:%S %Z')
            })
        st.dataframe(pd.DataFrame(df_raw_recent))


# Functions display_playlists and display_following are not in the main radio selection,
# but I'll keep them here if you plan to add them.
# Ensure they also use `ensure_valid_token(sp)` and similar error handling.

def display_playlists(sp):
    st.header("Your Playlists")
    sp = ensure_valid_token(sp)
    if not sp: return
    # ... (rest of the function, similar to others)

def display_following(sp):
    st.header("Artists You Follow")
    sp = ensure_valid_token(sp)
    if not sp: return
    # ... (rest of the function, similar to others)

# DB related functions (fetch_and_save_all_data, save_spotify_data)
# are assumed to be working and correctly imported if used.
# Make sure 'db_utils' is in your project structure or PYTHONPATH.
# from db_utils import upsert_user_document # Example import

def save_spotify_data(data_type, data):
    """Placeholder: Save Spotify data to MongoDB."""
    # from db_utils import upsert_user_document  # Import from your new file
    # user_id = st.session_state.spotify_user['id'] # Assuming spotify_user is in session
    # return upsert_user_document(user_id, data_type, data)
    st.toast(f"Data for {data_type} would be saved (DB logic pending).")
    print(f"Simulating save for {data_type}: {len(data)} items.")
    return True


def fetch_and_save_all_data(sp):
    sp = ensure_valid_token(sp)
    if not sp:
        st.sidebar.error("Cannot fetch data: Spotify connection invalid.")
        return False
    
    # Ensure user info is available for saving (if your DB schema needs it)
    if 'spotify_user' not in st.session_state or not st.session_state.spotify_user:
        try:
            st.session_state.spotify_user = sp.current_user()
        except Exception as e:
            st.sidebar.error(f"Could not get user info for DB save: {e}")
            return False

    all_success = True
    try:
        # Top Tracks
        for time_range in ["short_term", "medium_term", "long_term"]:
            top_tracks = sp.current_user_top_tracks(limit=50, time_range=time_range)
            if top_tracks['items']:
                # ... (data processing as in your original code) ...
                # For brevity, assuming tracks_data is prepared
                tracks_data_prepared = [{"Track": t['name'], "id": t['id']} for t in top_tracks['items']] # Simplified
                if not save_spotify_data(f'top_tracks_{time_range}', tracks_data_prepared): all_success = False
        
        # Top Artists
        for time_range in ["short_term", "medium_term", "long_term"]:
            top_artists = sp.current_user_top_artists(limit=50, time_range=time_range)
            if top_artists['items']:
                # ... (data processing) ...
                artists_data_prepared = [{"Artist": a['name'], "id": a['id']} for a in top_artists['items']] # Simplified
                if not save_spotify_data(f'top_artists_{time_range}', artists_data_prepared): all_success = False

        # Recently Played
        results = sp.current_user_recently_played(limit=50)
        if results['items']:
            # ... (data processing) ...
            recent_tracks_prepared = [{"Track": item['track']['name'], "id": item['track']['id']} for item in results['items']] # Simplified
            if not save_spotify_data('recently_played', recent_tracks_prepared): all_success = False
        
        # Add Playlists, Following etc. if needed
        
        return all_success
        
    except spotipy.exceptions.SpotifyException as e:
        st.sidebar.error(f"Spotify API error during data fetch for DB: {e}")
        return False
    except Exception as e:
        st.sidebar.error(f"Error fetching/saving data for DB: {e}")
        return False


if __name__ == "__main__":
    main()