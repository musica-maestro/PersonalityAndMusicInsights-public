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
            cache_path=".cache"  # Use a cache path - will be managed by session state
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
        return self.sp_oauth.get_authorize_url()
    
    def get_token_from_code(self, code):
        """Exchange authorization code for token"""
        try:
            token_info = self.sp_oauth.get_access_token(code)
            self.save_token_to_session(token_info)
            return token_info
        except Exception as e:
            st.error(f"Error getting token from code: {e}")
            return None

def get_spotify_oauth():
    """Function to get SpotifyOAuth instance - this was missing!"""
    return SpotifyOAuth(
        client_id=CLIENT_ID,
        client_secret=CLIENT_SECRET,
        redirect_uri=REDIRECT_URI,
        scope=SCOPE,
        cache_path=".cache"  # Use a cache path - will be ignored in our implementation
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
            st.rerun()
        else:
            st.error("Failed to authenticate with Spotify.")
    
    elif 'error' in query_params:
        error = query_params['error']
        st.error(f"Spotify authentication error: {error}")

def connect_to_spotify():
    """Connect to Spotify using browser-based auth"""
    try:
        # Handle OAuth callback first
        handle_callback()
        
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
            
            st.info("You'll be redirected back to this app automatically after authorization.")
            return None
        
        # Create Spotify client with valid token
        return spotipy.Spotify(auth=token_info['access_token'])
    
    except Exception as e:
        st.error(f"Error connecting to Spotify: {e}")
        return None

# Alternative: Using browser localStorage (requires JavaScript)
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
    """Clear Spotify authentication"""
    if 'spotify_token' in st.session_state:
        del st.session_state.spotify_token
    st.success("Successfully logged out from Spotify!")
    st.rerun()

# Main app function with logout option
def main():
    # Setup browser storage
    setup_browser_storage()
    
    # Add logout button in sidebar if authenticated
    if 'spotify_token' in st.session_state:
        st.sidebar.markdown("---")
        if st.sidebar.button("🚪 Logout from Spotify", type="secondary"):
            logout_spotify()
    
    sp = connect_to_spotify()
    
    if sp:
        try:
            # Test the connection
            user = sp.current_user()
            st.success(f"Successfully connected to Spotify! Welcome, {user['display_name']}!")
            
            # Store user info in session
            st.session_state.spotify_user = user
            
            # Create sidebar with options
            st.sidebar.title("Navigation")
            selection = st.sidebar.radio(
                "Information",
                ["Top Tracks", "Top Artists", "Recently Played"]
            )
            
            # Display selected content
            if selection == "Top Tracks":
                display_top_tracks(sp)
            elif selection == "Top Artists":
                display_top_artists(sp)
            elif selection == "Recently Played":
                display_recently_played(sp)
                
        except spotipy.exceptions.SpotifyException as e:
            st.error(f"Spotify API error: {e}")
            if "token expired" in str(e).lower():
                st.info("Your session has expired. Please reconnect to Spotify.")
                if st.button("Reconnect to Spotify"):
                    logout_spotify()
        except Exception as e:
            st.error(f"Unexpected error: {e}")

# Enhanced token validation
def validate_spotify_connection(sp):
    """Validate if Spotify connection is still valid"""
    try:
        sp.current_user()
        return True
    except spotipy.exceptions.SpotifyException:
        return False
    except Exception:
        return False

# Token refresh mechanism
def ensure_valid_token(sp):
    """Ensure token is valid, refresh if needed"""
    if not validate_spotify_connection(sp):
        auth = StreamlitSpotifyAuth()
        token_info = auth.get_token_from_session()
        
        if token_info:
            refreshed_token = auth.refresh_token(token_info)
            if refreshed_token:
                return spotipy.Spotify(auth=refreshed_token['access_token'])
        
        return None
    return sp

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
        }[x]
    )
    
    # Ensure valid token before API call
    sp = ensure_valid_token(sp)
    if not sp:
        st.error("Authentication expired. Please reconnect.")
        return
    
    top_tracks = sp.current_user_top_tracks(limit=50, time_range=time_range)
    
    if not top_tracks['items']:
        st.info("No top tracks found for this time period.")
        return
    
    tracks_data = []
    for i, track in enumerate(top_tracks['items'], 1):
        artists = ", ".join([artist['name'] for artist in track['artists']])
        album = track['album']['name']
        
        preview_url = track['preview_url']
        track_url = track['external_urls']['spotify']
        image_url = track['album']['images'][0]['url'] if track['album']['images'] else None
        
        tracks_data.append({
            "Rank": i,
            "Track": track['name'],
            "Artist(s)": artists,
            "Album": album,
            "Preview": preview_url,
            "Spotify Link": track_url,
            "Image": image_url,
            "track_id": track['id'],
            "time_range": time_range
        })
    
    # Display tracks in a grid (3 columns)
    cols = st.columns(3)
    for i, item in enumerate(tracks_data):
        with cols[i % 3]:
            st.image(item['Image'], width=150)
            st.write(f"**{i+1}. {item['Track']}**")
            st.write(f"by {item['Artist(s)']}")
            st.write(f"Album: {item['Album']}")
            if item['Preview']:
                st.audio(item['Preview'])
            st.markdown(f"[Open in Spotify]({item['Spotify Link']})")
            st.write("---")

# Function to display top artists
def display_top_artists(sp):
    st.header("Your Top Artists")
    
    time_range = st.radio(
        "Time Range",
        ["short_term", "medium_term", "long_term"],
        format_func=lambda x: {
            "short_term": "Last 4 Weeks",
            "medium_term": "Last 6 Months", 
            "long_term": "All Time"
        }[x]
    )
    
    top_artists = sp.current_user_top_artists(limit=50, time_range=time_range)
    
    if not top_artists['items']:
        st.info("No top artists found for this time period.")
        return
    
    artists_data = []
    for i, artist in enumerate(top_artists['items'], 1):
        genres = ", ".join(artist['genres']) if artist['genres'] else "Not specified"
        image_url = artist['images'][0]['url'] if artist['images'] else None
        
        artists_data.append({
            "Rank": i,
            "Artist": artist['name'],
            "Genres": genres,
            "Popularity": artist['popularity'],
            "Followers": artist['followers']['total'],
            "Spotify Link": artist['external_urls']['spotify'],
            "Image": image_url,
            "artist_id": artist['id'],
            "time_range": time_range
        })
    
    # Display in grid (3 columns)
    cols = st.columns(3)
    for i, item in enumerate(artists_data):
        with cols[i % 3]:
            st.image(item['Image'], width=150)
            st.write(f"**{i+1}. {item['Artist']}**")
            st.write(f"Genres: {item['Genres']}")
            st.write(f"Popularity: {item['Popularity']}/100")
            st.write(f"Followers: {item['Followers']:,}")
            st.markdown(f"[Open in Spotify]({item['Spotify Link']})")
            st.write("---")

# Function to display playlists
def display_playlists(sp):
    st.header("Your Playlists")
    
    playlists = sp.current_user_playlists(limit=50)
    
    if not playlists['items']:
        st.info("No playlists found.")
        return
    
    playlists_data = []
    for i, playlist in enumerate(playlists['items'], 1):
        # Get owner name
        owner = playlist['owner']['display_name']
        is_own = playlist['owner']['id'] == sp.current_user()['id']
        
        image_url = playlist['images'][0]['url'] if playlist['images'] else None
        
        playlists_data.append({
            "Rank": i,
            "Name": playlist['name'],
            "Tracks": playlist['tracks']['total'],
            "Owner": "You" if is_own else owner,
            "Public": "Yes" if playlist['public'] else "No",
            "Collaborative": "Yes" if playlist['collaborative'] else "No",
            "Spotify Link": playlist['external_urls']['spotify'],
            "Image": image_url,
            "playlist_id": playlist['id']
        })
    
    # Display in grid (3 columns)
    cols = st.columns(3)
    for i, item in enumerate(playlists_data):
        with cols[i % 3]:
            st.image(item['Image'], width=150)
            st.write(f"**{item['Name']}**")
            st.write(f"Tracks: {item['Tracks']}")
            st.write(f"Owner: {item['Owner']}")
            st.write(f"Public: {item['Public']}")
            st.markdown(f"[Open in Spotify]({item['Spotify Link']})")
            st.write("---")

# Function to display followed artists
def display_following(sp):
    st.header("Artists You Follow")
    
    following = sp.current_user_followed_artists(limit=50)
    
    if not following['artists']['items']:
        st.info("You don't follow any artists.")
        return
    
    following_data = []
    for i, artist in enumerate(following['artists']['items'], 1):
        genres = ", ".join(artist['genres']) if artist['genres'] else "Not specified"
        image_url = artist['images'][0]['url'] if artist['images'] else None
        
        following_data.append({
            "Rank": i,
            "Artist": artist['name'],
            "Genres": genres,
            "Popularity": artist['popularity'],
            "Followers": artist['followers']['total'],
            "Spotify Link": artist['external_urls']['spotify'],
            "Image": image_url,
            "artist_id": artist['id']
        })
    
    # Display in grid (3 columns)
    cols = st.columns(3)
    for i, item in enumerate(following_data):
        with cols[i % 3]:
            st.image(item['Image'], width=150)
            st.write(f"**{item['Artist']}**")
            st.write(f"Genres: {item['Genres']}")
            st.write(f"Popularity: {item['Popularity']}/100")
            st.write(f"Followers: {item['Followers']:,}")
            st.markdown(f"[Open in Spotify]({item['Spotify Link']})")
            st.write("---")

# Function to display recently played tracks
def display_recently_played(sp):
    st.header("Your Recently Played Tracks")
    
    results = sp.current_user_recently_played(limit=50)
    
    if not results['items']:
        st.info("No recently played tracks found.")
        return
    
    # Extract data for display
    tracks_data = []
    for i, item in enumerate(results['items'], 1):
        track = item['track']
        played_at = item['played_at']

        # Convert UTC time to Rome time
        utc_time = datetime.strptime(played_at, '%Y-%m-%dT%H:%M:%S.%fZ')
        utc_time = utc_time.replace(tzinfo=pytz.UTC)
        rome_tz = pytz.timezone('Europe/Rome')
        rome_time = utc_time.astimezone(rome_tz)
        played_at_local = rome_time.strftime('%Y-%m-%d %H:%M:%S')
        
        # Get track details
        artists = ", ".join([artist['name'] for artist in track['artists']])
        album = track['album']['name']
        preview_url = track['preview_url']
        track_url = track['external_urls']['spotify']
        image_url = track['album']['images'][0]['url'] if track['album']['images'] else None
        
        tracks_data.append({
            "Track": track['name'],
            "Artist(s)": artists,
            "Album": album,
            "Played At": played_at_local,
            "Preview": preview_url,
            "Spotify Link": track_url,
            "Image": image_url
        })
    
    # Display in grid (3 columns)
    cols = st.columns(3)
    for i, item in enumerate(tracks_data):
        with cols[i % 3]:
            st.image(item['Image'], width=150)
            st.write(f"**{item['Track']}**")
            st.write(f"by {item['Artist(s)']}")
            st.write(f"Album: {item['Album']}")
            st.write(f"Played at: {item['Played At']}")
            if item['Preview']:
                st.audio(item['Preview'])
            st.markdown(f"[Open in Spotify]({item['Spotify Link']})")
            st.write("---")
    
    # Display raw data in expander
    with st.expander("View as table"):
        st.dataframe(pd.DataFrame(tracks_data))

def save_spotify_data(data_type, data):
    """Save Spotify data to MongoDB."""
    from db_utils import upsert_user_document  # Import from your new file
    return upsert_user_document(data_type, data)

# Fetch and save all Spotify data
def fetch_and_save_all_data(sp):
    try:
        # Top Tracks (for all time ranges)
        for time_range in ["short_term", "medium_term", "long_term"]:
            top_tracks = sp.current_user_top_tracks(limit=50, time_range=time_range)
            if top_tracks['items']:
                tracks_data = []
                for i, track in enumerate(top_tracks['items'], 1):
                    artists = ", ".join([artist['name'] for artist in track['artists']])
                    album = track['album']['name']
                    preview_url = track['preview_url']
                    track_url = track['external_urls']['spotify']
                    image_url = track['album']['images'][0]['url'] if track['album']['images'] else None
                    
                    tracks_data.append({
                        "Rank": i,
                        "Track": track['name'],
                        "Artist(s)": artists,
                        "Album": album,
                        "Preview": preview_url,
                        "Spotify Link": track_url,
                        "Image": image_url,
                        "track_id": track['id'],
                        "time_range": time_range,
                        "snapshot_date": datetime.now()
                    })
                
                # Save top tracks using the imported MongoDB function
                #save_to_mongodb('top_tracks', tracks_data, ['track_id', 'time_range', 'snapshot_date'])
                save_spotify_data('top_tracks_'+ time_range, tracks_data)

        # Top Artists (for all time ranges)
        for time_range in ["short_term", "medium_term", "long_term"]:
            top_artists = sp.current_user_top_artists(limit=50, time_range=time_range)
            if top_artists['items']:
                artists_data = []
                for i, artist in enumerate(top_artists['items'], 1):
                    genres = ", ".join(artist['genres']) if artist['genres'] else "Not specified"
                    image_url = artist['images'][0]['url'] if artist['images'] else None
                    
                    artists_data.append({
                        "Rank": i,
                        "Artist": artist['name'],
                        "Genres": genres,
                        "Popularity": artist['popularity'],
                        "Followers": artist['followers']['total'],
                        "Spotify Link": artist['external_urls']['spotify'],
                        "Image": image_url,
                        "artist_id": artist['id'],
                        "time_range": time_range,
                        "snapshot_date": datetime.now()
                    })
                
                # Save top artists
                #save_to_mongodb('top_artists', artists_data, ['artist_id', 'time_range', 'snapshot_date'])
                save_spotify_data('top_artists_'+time_range, artists_data)

        # Playlists
        playlists = sp.current_user_playlists(limit=50)
        if playlists['items']:
            playlists_data = []
            for i, playlist in enumerate(playlists['items'], 1):
                owner = playlist['owner']['display_name']
                is_own = playlist['owner']['id'] == sp.current_user()['id']
                image_url = playlist['images'][0]['url'] if playlist['images'] else None
                
                playlists_data.append({
                    "Rank": i,
                    "Name": playlist['name'],
                    "Tracks": playlist['tracks']['total'],
                    "Owner": "You" if is_own else owner,
                    "Public": "Yes" if playlist['public'] else "No",
                    "Collaborative": "Yes" if playlist['collaborative'] else "No",
                    "Spotify Link": playlist['external_urls']['spotify'],
                    "Image": image_url,
                    "playlist_id": playlist['id'],
                    "snapshot_date": datetime.now()
                })
            
            # Save playlists
            #save_to_mongodb('playlists', playlists_data, ['playlist_id', 'snapshot_date'])
            save_spotify_data('playlists', playlists_data)
        
        # Following
        following = sp.current_user_followed_artists(limit=50)
        if following['artists']['items']:
            following_data = []
            for i, artist in enumerate(following['artists']['items'], 1):
                genres = ", ".join(artist['genres']) if artist['genres'] else "Not specified"
                image_url = artist['images'][0]['url'] if artist['images'] else None
                
                following_data.append({
                    "Rank": i,
                    "Artist": artist['name'],
                    "Genres": genres,
                    "Popularity": artist['popularity'],
                    "Followers": artist['followers']['total'],
                    "Spotify Link": artist['external_urls']['spotify'],
                    "Image": image_url,
                    "artist_id": artist['id'],
                    "snapshot_date": datetime.now()
                })
            
            # Save following
            #save_to_mongodb('following', following_data, ['artist_id', 'snapshot_date'])
            save_spotify_data('following', following_data)
        
        # Recently Played
        results = sp.current_user_recently_played(limit=50)
        if results['items']:
            recent_tracks = []
            for item in results['items']:
                track = item['track']
                played_at = item['played_at']
                
                # Convert UTC time to Rome time
                utc_time = datetime.strptime(played_at, '%Y-%m-%dT%H:%M:%S.%fZ')
                utc_time = utc_time.replace(tzinfo=pytz.UTC)
                rome_tz = pytz.timezone('Europe/Rome')
                rome_time = utc_time.astimezone(rome_tz)
                played_at_local = rome_time.strftime('%Y-%m-%d %H:%M:%S')
                
                track_data = {
                    'track_name': track['name'],
                    'track_id': track['id'],
                    'artist_name': track['artists'][0]['name'],
                    'artist_id': track['artists'][0]['id'],
                    'album_name': track['album']['name'],
                    'album_id': track['album']['id'],
                    'played_at': played_at,
                    'played_at_local': played_at_local,
                    'external_url': track['external_urls']['spotify'],
                    'snapshot_date': datetime.now()
                }
                recent_tracks.append(track_data)
            
            # Save recently played
            #save_to_mongodb('recently_played', recent_tracks, ['track_id', 'played_at'])
            save_spotify_data('recently_played', recent_tracks)
        
        
        return True
        
    except Exception as e:
        st.sidebar.error(f"Error fetching data: {e}")
        return False