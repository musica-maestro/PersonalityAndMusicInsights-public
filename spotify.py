import streamlit as st
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import pandas as pd
import time
from datetime import datetime, timedelta
import pytz
# import json # Not used directly in the provided snippet after changes
# import base64 # Not used
# from urllib.parse import parse_qs, urlparse # Not used directly

# Spotify API credentials
CLIENT_ID = st.secrets["spotify"]["client_id"]
CLIENT_SECRET = st.secrets["spotify"]["client_secret"]
REDIRECT_URI = st.secrets["spotify"]["redirect_uri"]
SCOPE = "user-read-private user-read-email user-top-read user-follow-read playlist-read-private user-read-recently-played"

# --- Custom Cache Handler for Streamlit Session State ---
class SessionStateCacheHandler:
    def __init__(self, session_key="spotify_token_info"):
        self.session_key = session_key

    def get_cached_token(self):
        return st.session_state.get(self.session_key, None)

    def save_token_to_cache(self, token_info):
        st.session_state[self.session_key] = token_info
    
    def clear_cached_token(self):
        if self.session_key in st.session_state:
            del st.session_state[self.session_key]

# --- Spotify Authentication Class for Streamlit ---
class StreamlitSpotifyAuth:
    SESSION_TOKEN_KEY = "spotify_token_info"  # Key for storing token in st.session_state

    def __init__(self):
        self.client_id = CLIENT_ID
        self.client_secret = CLIENT_SECRET
        self.redirect_uri = REDIRECT_URI
        self.scope = SCOPE
        
        self.cache_handler = SessionStateCacheHandler(session_key=self.SESSION_TOKEN_KEY)
        
        self.sp_oauth = SpotifyOAuth(
            client_id=self.client_id,
            client_secret=self.client_secret,
            redirect_uri=self.redirect_uri,
            scope=self.scope,
            cache_handler=self.cache_handler,
            # cache_path=None # Explicitly set to None as cache_handler is used
        )

    def get_auth_url(self):
        """Get authorization URL"""
        return self.sp_oauth.get_authorize_url()

    def get_token_from_code(self, code):
        """Exchange authorization code for token. Token is saved by cache_handler."""
        try:
            token_info = self.sp_oauth.get_access_token(code, check_cache=False)
            return token_info
        except Exception as e:
            st.error(f"Error getting token from code: {e}")
            self.cache_handler.clear_cached_token() # Clear potentially corrupt state
            return None

    def get_valid_token_info(self):
        """
        Retrieves token info from session state using the cache handler.
        If a token exists, it validates it (which includes refreshing if necessary).
        Returns valid token_info or None.
        """
        token_info = self.cache_handler.get_cached_token()
        if not token_info:
            return None

        # SpotifyOAuth.validate_token checks expiry and attempts refresh if needed.
        # If refreshed, the new token is saved back to cache via the cache_handler.
        validated_token_info = self.sp_oauth.validate_token(token_info)
        
        if not validated_token_info:
            # Token was invalid and could not be refreshed. Clear it.
            self.cache_handler.clear_cached_token()
            return None
        
        return validated_token_info # This is the (original or refreshed) token_info
    
    def clear_session_token(self):
        """Clears the token from the session state via the cache handler."""
        self.cache_handler.clear_cached_token()

# --- Authentication Flow Functions ---
def handle_oauth_callback():
    """Handle OAuth callback from URL parameters."""
    query_params = st.query_params
    
    if 'code' in query_params:
        code = query_params['code']
        # Use a fresh auth instance for the callback process
        auth_manager = StreamlitSpotifyAuth() 
        token_info = auth_manager.get_token_from_code(code)
        
        if token_info:
            st.success("Successfully authenticated with Spotify!")
            # Token is now in session_state. Clear URL params and rerun.
            st.query_params.clear() 
            st.rerun()
        else:
            st.error("Failed to authenticate with Spotify. The authorization code might be invalid or expired.")
            # Attempt to remove only the 'code' query parameter to avoid loops on refresh
            # but allow other params to persist if necessary.
            # However, for this flow, clearing all is usually fine.
            st.query_params.clear() 
            # No rerun here, let the user see the error. They might need to retry auth.
    
    elif 'error' in query_params:
        error_message = query_params.get('error', "Unknown error during Spotify authentication.")
        st.error(f"Spotify authentication error: {error_message}")
        st.query_params.clear() # Clear error from URL

def connect_to_spotify():
    """
    Manages Spotify connection: handles OAuth callback, gets/validates token,
    or shows connect button.
    Returns an authenticated Spotipy client or None.
    """
    # Handle OAuth callback first (if `code` or `error` in URL)
    # This might rerun the app if authentication is successful.
    handle_oauth_callback() 
    
    auth_manager = StreamlitSpotifyAuth()
    token_info = auth_manager.get_valid_token_info() # Retrieves from session, validates, refreshes
    
    if not token_info:
        st.markdown("### Connect to Spotify")
        st.write("Please click the button below to authorize this app to access your Spotify data:")
        
        auth_url = auth_manager.get_auth_url()
        
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
        
        st.info("You'll be redirected back to this app automatically after authorization.")
        return None # No authenticated client yet
    
    # Create Spotify client with valid access token
    return spotipy.Spotify(auth=token_info['access_token'])

def get_spotify_client():
    """Convenience function to get authenticated Spotify client."""
    return connect_to_spotify()

# --- Logout Function ---
def logout_spotify():
    """Clear Spotify authentication from session state and rerun."""
    auth_manager = StreamlitSpotifyAuth()
    auth_manager.clear_session_token()
    
    # Clear any other user-specific data from session if needed
    if 'spotify_user' in st.session_state:
        del st.session_state.spotify_user
        
    st.success("Successfully logged out from Spotify!")
    st.rerun()

# --- Browser localStorage (JavaScript) - Unchanged as it's not directly tied to Python auth logic ---
def setup_browser_storage():
    """Setup browser localStorage for token storage (JS side, not directly used by Python token flow)"""
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

# --- Main App Function ---
def main():
    st.set_page_config(page_title="Spotify Insights", layout="wide")
    st.title("🎧 Your Spotify Insights")

    # Setup browser storage (if you plan to use JS localStorage for other purposes)
    # This is not directly used for the Python-driven auth token persistence.
    setup_browser_storage() 
    
    # Add logout button in sidebar if authenticated
    # Check using the session key defined in StreamlitSpotifyAuth
    if StreamlitSpotifyAuth.SESSION_TOKEN_KEY in st.session_state and st.session_state[StreamlitSpotifyAuth.SESSION_TOKEN_KEY]:
        st.sidebar.markdown("---")
        # Using on_click for button action is cleaner
        st.sidebar.button("🚪 Logout from Spotify", type="secondary", on_click=logout_spotify)
    
    sp = get_spotify_client() # This now incorporates the full auth logic
    
    if sp:
        try:
            user = sp.current_user()
            st.success(f"Successfully connected to Spotify! Welcome, {user['display_name']}!")
            st.session_state.spotify_user = user # Store user info
            
            st.sidebar.title("Navigation")
            selection = st.sidebar.radio(
                "Explore Your Music", # Changed label for clarity
                ["Top Tracks", "Top Artists", "Recently Played", "Your Playlists", "Followed Artists"] # Added more options
            )
            
            if selection == "Top Tracks":
                display_top_tracks(sp)
            elif selection == "Top Artists":
                display_top_artists(sp)
            elif selection == "Recently Played":
                display_recently_played(sp)
            elif selection == "Your Playlists": # Added from your original code
                display_playlists(sp)
            elif selection == "Followed Artists": # Added from your original code
                display_following(sp)

            # Optional: Button to fetch and save all data to DB
            # This part is intensive, consider user feedback (e.g. progress bar)
            st.sidebar.markdown("---")
            if st.sidebar.button("🔄 Sync All My Spotify Data"):
                with st.spinner("Fetching and saving all your Spotify data... This might take a moment."):
                    if fetch_and_save_all_data(sp):
                        st.sidebar.success("All data synced successfully!")
                    else:
                        st.sidebar.error("Failed to sync all data.")
                
        except spotipy.exceptions.SpotifyException as e:
            st.error(f"Spotify API error: {e}")
            if "token expired" in str(e).lower() or "invalid access token" in str(e).lower():
                st.info("Your Spotify session has expired or is invalid. Please reconnect.")
                # Clearing the token and rerunning will prompt re-authentication.
                if st.button("Reconnect to Spotify"):
                    logout_spotify() 
            # For other Spotify errors, you might want different handling
        except Exception as e:
            st.error(f"An unexpected error occurred: {e}")
            st.exception(e) # Provides more details for debugging

# --- Display Functions (Ensure they use the passed 'sp' client) ---
# No changes needed to the display functions themselves if they correctly use the 'sp'
# object passed to them and don't try to re-authenticate internally.
# The ensure_valid_token calls are removed from them as connect_to_spotify and main's error handling cover this.

def display_top_tracks(sp):
    st.header("Your Top Tracks")
    time_range = st.radio(
        "Select Time Range:", # Clearer label
        ["short_term", "medium_term", "long_term"],
        format_func=lambda x: {"short_term": "Last 4 Weeks", "medium_term": "Last 6 Months", "long_term": "All Time"}[x],
        key="top_tracks_time_range" # Unique key for radio
    )
    
    try:
        top_tracks = sp.current_user_top_tracks(limit=50, time_range=time_range)
    except spotipy.exceptions.SpotifyException as e:
        st.error(f"Could not load top tracks: {e}")
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
        image_url = track['album']['images'][0]['url'] if track['album']['images'] else "https://placehold.co/150x150?text=No+Image"
        
        tracks_data.append({
            "Rank": i, "Track": track['name'], "Artist(s)": artists, "Album": album,
            "Preview": preview_url, "Spotify Link": track_url, "Image": image_url,
            "track_id": track['id'], "time_range": time_range
        })
    
    cols = st.columns(3)
    for i, item in enumerate(tracks_data):
        with cols[i % 3]:
            st.image(item['Image'], width=150, caption=f"{item['Track']} by {item['Artist(s)']}")
            st.markdown(f"**{i+1}. {item['Track']}**")
            st.markdown(f"_{item['Artist(s)']}_")
            st.markdown(f"Album: {item['Album']}")
            if item['Preview']:
                st.audio(item['Preview'], format="audio/mp3", start_time=0)
            st.link_button("Open in Spotify", item['Spotify Link'])
            st.markdown("---")

def display_top_artists(sp):
    st.header("Your Top Artists")
    time_range = st.radio(
        "Select Time Range:", # Clearer label
        ["short_term", "medium_term", "long_term"],
        format_func=lambda x: {"short_term": "Last 4 Weeks", "medium_term": "Last 6 Months", "long_term": "All Time"}[x],
        key="top_artists_time_range" # Unique key
    )

    try:
        top_artists = sp.current_user_top_artists(limit=50, time_range=time_range)
    except spotipy.exceptions.SpotifyException as e:
        st.error(f"Could not load top artists: {e}")
        return

    if not top_artists['items']:
        st.info("No top artists found for this time period.")
        return
    
    artists_data = []
    for i, artist in enumerate(top_artists['items'], 1):
        genres = ", ".join(artist['genres']) if artist['genres'] else "Not specified"
        image_url = artist['images'][0]['url'] if artist['images'] else "https://placehold.co/150x150?text=No+Image"
        
        artists_data.append({
            "Rank": i, "Artist": artist['name'], "Genres": genres,
            "Popularity": artist['popularity'], "Followers": artist['followers']['total'],
            "Spotify Link": artist['external_urls']['spotify'], "Image": image_url,
            "artist_id": artist['id'], "time_range": time_range
        })
    
    cols = st.columns(3)
    for i, item in enumerate(artists_data):
        with cols[i % 3]:
            st.image(item['Image'], width=150, caption=item['Artist'])
            st.markdown(f"**{i+1}. {item['Artist']}**")
            st.markdown(f"Genres: {item['Genres']}")
            st.markdown(f"Popularity: {item['Popularity']}/100")
            st.markdown(f"Followers: {item['Followers']:,}")
            st.link_button("Open in Spotify", item['Spotify Link'])
            st.markdown("---")

def display_playlists(sp):
    st.header("Your Playlists")
    try:
        playlists = sp.current_user_playlists(limit=50)
    except spotipy.exceptions.SpotifyException as e:
        st.error(f"Could not load playlists: {e}")
        return

    if not playlists['items']:
        st.info("No playlists found.")
        return
    
    playlists_data = []
    current_user_id = st.session_state.get('spotify_user', {}).get('id') # Get current user ID
    for i, playlist in enumerate(playlists['items'], 1):
        owner = playlist['owner']['display_name']
        is_own = current_user_id and playlist['owner']['id'] == current_user_id
        image_url = playlist['images'][0]['url'] if playlist['images'] else "https://placehold.co/150x150?text=No+Image"
        
        playlists_data.append({
            "Rank": i, "Name": playlist['name'], "Tracks": playlist['tracks']['total'],
            "Owner": "You" if is_own else owner,
            "Public": "Yes" if playlist['public'] else "No",
            "Collaborative": "Yes" if playlist['collaborative'] else "No",
            "Spotify Link": playlist['external_urls']['spotify'], "Image": image_url,
            "playlist_id": playlist['id']
        })
    
    cols = st.columns(3)
    for i, item in enumerate(playlists_data):
        with cols[i % 3]:
            st.image(item['Image'], width=150, caption=item['Name'])
            st.markdown(f"**{item['Name']}**")
            st.markdown(f"Tracks: {item['Tracks']}")
            st.markdown(f"Owner: {item['Owner']}")
            st.markdown(f"Public: {item['Public']}")
            st.link_button("Open in Spotify", item['Spotify Link'])
            st.markdown("---")

def display_following(sp):
    st.header("Artists You Follow")
    try:
        following = sp.current_user_followed_artists(limit=50)
    except spotipy.exceptions.SpotifyException as e:
        st.error(f"Could not load followed artists: {e}")
        return

    if not following['artists']['items']:
        st.info("You don't follow any artists.")
        return
    
    following_data = []
    for i, artist in enumerate(following['artists']['items'], 1):
        genres = ", ".join(artist['genres']) if artist['genres'] else "Not specified"
        image_url = artist['images'][0]['url'] if artist['images'] else "https://placehold.co/150x150?text=No+Image"
        
        following_data.append({
            "Rank": i, "Artist": artist['name'], "Genres": genres,
            "Popularity": artist['popularity'], "Followers": artist['followers']['total'],
            "Spotify Link": artist['external_urls']['spotify'], "Image": image_url,
            "artist_id": artist['id']
        })
    
    cols = st.columns(3)
    for i, item in enumerate(following_data):
        with cols[i % 3]:
            st.image(item['Image'], width=150, caption=item['Artist'])
            st.markdown(f"**{item['Artist']}**")
            st.markdown(f"Genres: {item['Genres']}")
            st.markdown(f"Popularity: {item['Popularity']}/100")
            st.markdown(f"Followers: {item['Followers']:,}")
            st.link_button("Open in Spotify", item['Spotify Link'])
            st.markdown("---")

def display_recently_played(sp):
    st.header("Your Recently Played Tracks")
    try:
        results = sp.current_user_recently_played(limit=50)
    except spotipy.exceptions.SpotifyException as e:
        st.error(f"Could not load recently played tracks: {e}")
        return

    if not results['items']:
        st.info("No recently played tracks found.")
        return
    
    tracks_data = []
    for i, item in enumerate(results['items'], 1):
        track = item['track']
        played_at_utc_str = item['played_at'] # ISO format string: '%Y-%m-%dT%H:%M:%S.%fZ'
        
        utc_time = datetime.strptime(played_at_utc_str, '%Y-%m-%dT%H:%M:%S.%fZ').replace(tzinfo=pytz.utc)
        rome_tz = pytz.timezone('Europe/Rome')
        rome_time = utc_time.astimezone(rome_tz)
        played_at_local = rome_time.strftime('%Y-%m-%d %H:%M:%S %Z') # Include timezone abbr
        
        artists = ", ".join([artist['name'] for artist in track['artists']])
        album = track['album']['name']
        preview_url = track['preview_url']
        track_url = track['external_urls']['spotify']
        image_url = track['album']['images'][0]['url'] if track['album']['images'] else "https://placehold.co/150x150?text=No+Image"
        
        tracks_data.append({
            "Track": track['name'], "Artist(s)": artists, "Album": album,
            "Played At (Local)": played_at_local, "Preview": preview_url,
            "Spotify Link": track_url, "Image": image_url
        })
    
    cols = st.columns(3)
    for i, item in enumerate(tracks_data):
        with cols[i % 3]:
            st.image(item['Image'], width=150, caption=f"{item['Track']} by {item['Artist(s)']}")
            st.markdown(f"**{item['Track']}**")
            st.markdown(f"_{item['Artist(s)']}_")
            st.markdown(f"Album: {item['Album']}")
            st.caption(f"Played: {item['Played At (Local)']}")
            if item['Preview']:
                st.audio(item['Preview'], format="audio/mp3", start_time=0)
            st.link_button("Open in Spotify", item['Spotify Link'])
            st.markdown("---")
    
    with st.expander("View as table"):
        st.dataframe(pd.DataFrame(tracks_data).drop(columns=['Image', 'Preview', 'Spotify Link'])) # Cleaner table

# --- Data Saving (MongoDB related - ensure db_utils.py exists) ---
def save_spotify_data(data_type, data):
    """Save Spotify data to MongoDB."""
    try:
        from db_utils import upsert_user_document # Assuming db_utils.py is in the same directory
        # You might want to add user_id to the data before saving if upsert_user_document expects it
        # e.g., user_id = st.session_state.spotify_user['id']
        return upsert_user_document(data_type, data) 
    except ImportError:
        st.error("db_utils.py not found. Cannot save data to MongoDB.")
        return False
    except Exception as e:
        st.error(f"Error saving data to MongoDB ({data_type}): {e}")
        return False

def fetch_and_save_all_data(sp):
    """Fetch various Spotify data points and save them using save_spotify_data."""
    if not sp:
        st.error("Spotify client not available. Cannot fetch data.")
        return False
    
    current_user_id = st.session_state.get('spotify_user', {}).get('id')
    if not current_user_id:
        st.error("User ID not found in session. Cannot associate data.")
        return False

    all_successful = True
    now = datetime.now(pytz.utc) # Use timezone-aware datetime

    # Helper function to add user_id and snapshot_date
    def enrich_data(items_list, item_type):
        enriched = []
        for item in items_list:
            item['user_id'] = current_user_id
            item['snapshot_utc'] = now.isoformat() 
            item['item_type'] = item_type # For easier querying in DB
            enriched.append(item)
        return enriched

    try:
        # Top Tracks
        for time_range in ["short_term", "medium_term", "long_term"]:
            top_tracks_raw = sp.current_user_top_tracks(limit=50, time_range=time_range)
            if top_tracks_raw['items']:
                tracks_data = enrich_data(top_tracks_raw['items'], f"top_track_{time_range}")
                if not save_spotify_data(f'user_top_tracks_{time_range}', tracks_data): all_successful = False
        
        # Top Artists
        for time_range in ["short_term", "medium_term", "long_term"]:
            top_artists_raw = sp.current_user_top_artists(limit=50, time_range=time_range)
            if top_artists_raw['items']:
                artists_data = enrich_data(top_artists_raw['items'], f"top_artist_{time_range}")
                if not save_spotify_data(f'user_top_artists_{time_range}', artists_data): all_successful = False
        
        # Playlists
        playlists_raw = sp.current_user_playlists(limit=50)
        if playlists_raw['items']:
            playlists_data = enrich_data(playlists_raw['items'], "playlist")
            if not save_spotify_data('user_playlists', playlists_data): all_successful = False
        
        # Followed Artists
        following_raw = sp.current_user_followed_artists(limit=50)
        if following_raw['artists']['items']:
            following_data = enrich_data(following_raw['artists']['items'], "followed_artist")
            if not save_spotify_data('user_followed_artists', following_data): all_successful = False
        
        # Recently Played
        recent_raw = sp.current_user_recently_played(limit=50)
        if recent_raw['items']:
            # played_at is already part of the item, ensure it's UTC
            recent_tracks = enrich_data(recent_raw['items'], "recently_played")
            if not save_spotify_data('user_recently_played', recent_tracks): all_successful = False
        
        return all_successful
        
    except spotipy.exceptions.SpotifyException as e:
        st.sidebar.error(f"Spotify API error during data sync: {e}")
        return False
    except Exception as e:
        st.sidebar.error(f"Unexpected error during data sync: {e}")
        st.exception(e)
        return False

# --- Run the App ---
if __name__ == '__main__':
    main()