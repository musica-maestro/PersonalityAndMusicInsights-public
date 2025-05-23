import streamlit as st
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import pandas as pd
import time
from datetime import datetime
import pytz
import urllib.parse

# Spotify API credentials
CLIENT_ID = st.secrets["spotify"]["client_id"]
CLIENT_SECRET = st.secrets["spotify"]["client_secret"]
REDIRECT_URI = st.secrets["spotify"]["redirect_uri"]
SCOPE = "user-read-private user-read-email user-top-read user-follow-read playlist-read-private user-read-recently-played"

# Function to create Spotify OAuth client
def get_spotify_oauth():
    return SpotifyOAuth(
        client_id=CLIENT_ID,
        client_secret=CLIENT_SECRET,
        redirect_uri=REDIRECT_URI,
        scope=SCOPE,
        cache_path=None  # Disable file cache
    )

def redirect_to_spotify_auth():
    """Redirect user to Spotify authorization page"""
    sp_oauth = get_spotify_oauth()
    auth_url = sp_oauth.get_authorize_url()
    
    # Use JavaScript to redirect immediately
    st.markdown(f"""
    <script>
        window.location.href = "{auth_url}";
    </script>
    """, unsafe_allow_html=True)
    
    # Fallback message in case JavaScript doesn't work
    st.info("Redirecting to Spotify authorization...")
    st.markdown(f'<meta http-equiv="refresh" content="0; url={auth_url}">', unsafe_allow_html=True)

def connect_to_spotify():
    try:
        sp_oauth = get_spotify_oauth()
        
        # Check if we have token info in session state
        if 'spotify_token_info' in st.session_state:
            token_info = st.session_state.spotify_token_info
            
            # Check if token is expired and refresh if needed
            if sp_oauth.is_token_expired(token_info):
                try:
                    token_info = sp_oauth.refresh_access_token(token_info['refresh_token'])
                    st.session_state.spotify_token_info = token_info
                except Exception:
                    # If refresh fails, redirect to Spotify auth
                    if 'spotify_token_info' in st.session_state:
                        del st.session_state.spotify_token_info
                    redirect_to_spotify_auth()
                    return None
            
            # Create and return Spotify client
            return spotipy.Spotify(auth=token_info['access_token'])
        
        # Check if we're returning from Spotify authorization
        query_params = st.query_params
        if 'code' in query_params:
            auth_code = query_params['code']
            try:
                # Exchange code for token
                token_info = sp_oauth.get_access_token(auth_code)
                if token_info:
                    # Store token in session state
                    st.session_state.spotify_token_info = token_info
                    # Clear the URL parameters and rerun
                    st.query_params.clear()
                    st.rerun()
                else:
                    # If token exchange fails, redirect to auth
                    redirect_to_spotify_auth()
                    return None
            except Exception:
                # If any error during token exchange, redirect to auth
                redirect_to_spotify_auth()
                return None
        
        # If no token and no code, redirect to Spotify auth
        redirect_to_spotify_auth()
        return None
        
    except Exception:
        # For any connection error, redirect to Spotify auth
        redirect_to_spotify_auth()
        return None

# Main app function
def main():
    # Initialize Spotify connection
    if 'sp' not in st.session_state:
        st.session_state.sp = connect_to_spotify()
    
    sp = st.session_state.sp
    
    if sp:
        try:
            # Test the connection by getting user info
            user_info = sp.current_user()
            st.success(f"Successfully connected to Spotify! Welcome, {user_info.get('display_name', 'User')}!")
            
            # Add a disconnect button in the sidebar
            if st.sidebar.button("🔓 Disconnect from Spotify"):
                # Clear session state
                if 'spotify_token_info' in st.session_state:
                    del st.session_state.spotify_token_info
                if 'sp' in st.session_state:
                    del st.session_state.sp
                st.rerun()
            
            # Create sidebar with options
            st.sidebar.title("Navigation")
            selection = st.sidebar.radio(
                "Information",
                ["Top Tracks", "Top Artists", "Recently Played"]
            )
            
            # Display top tracks
            if selection == "Top Tracks":
                display_top_tracks(sp)
            # Display top artists
            elif selection == "Top Artists":
                display_top_artists(sp)
            # Display recently played tracks
            elif selection == "Recently Played":
                display_recently_played(sp)
                
        except Exception:
            # If any error with the Spotify client, redirect to auth
            if 'spotify_token_info' in st.session_state:
                del st.session_state.spotify_token_info
            if 'sp' in st.session_state:
                del st.session_state.sp
            redirect_to_spotify_auth()
    else:
        # This will be handled by the redirect in connect_to_spotify()
        st.info("Connecting to Spotify...")

# Function to display top tracks
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
    
    try:
        top_tracks = sp.current_user_top_tracks(limit=50, time_range=time_range)
    except Exception:
        # If API call fails, redirect to auth
        redirect_to_spotify_auth()
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
            if item['Image']:
                st.image(item['Image'], width=150)
            st.write(f"{i+1}. {item['Track']}")
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
    
    try:
        top_artists = sp.current_user_top_artists(limit=50, time_range=time_range)
    except Exception:
        # If API call fails, redirect to auth
        redirect_to_spotify_auth()
        return
    
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
            if item['Image']:
                st.image(item['Image'], width=150)
            st.write(f"{i+1}. {item['Artist']}")
            st.write(f"Genres: {item['Genres']}")
            st.write(f"Popularity: {item['Popularity']}/100")
            st.write(f"Followers: {item['Followers']:,}")
            st.markdown(f"[Open in Spotify]({item['Spotify Link']})")
            st.write("---")

# Function to display recently played tracks
def display_recently_played(sp):
    st.header("Your Recently Played Tracks")
    
    try:
        results = sp.current_user_recently_played(limit=50)
    except Exception:
        # If API call fails, redirect to auth
        redirect_to_spotify_auth()
        return
    
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
            if item['Image']:
                st.image(item['Image'], width=150)
            st.write(f"{item['Track']}")
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
    from db_utils import upsert_user_document
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
                
                save_spotify_data('top_artists_'+time_range, artists_data)
        
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
            
            save_spotify_data('recently_played', recent_tracks)
        
        return True
    except Exception as e:
        st.sidebar.error(f"Error fetching data: {e}")
        return False

if __name__ == "__main__":
    main()