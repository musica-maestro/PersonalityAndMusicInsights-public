# Updated spotify.py
import streamlit as st
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import pandas as pd
import time
from datetime import datetime
import pytz
#from db_utils import save_to_mongodb  # Import from db_utils instead of webapp

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
        cache_path=".spotifycache"
    )

def connect_to_spotify():
    try:
        sp_oauth = get_spotify_oauth()
        token_info = sp_oauth.get_cached_token()
        
        if not token_info:
            auth_url = sp_oauth.get_authorize_url()
            st.markdown(f"### Connect to Spotify")
            st.write("Please click the button below to authorize this app to access your Spotify data:")
            st.markdown(f"<a href='{auth_url}' target='_self'><button style='background-color:#1DB954; color:white; padding:10px 20px; border:none; border-radius:30px; font-weight:bold;'>Connect to Spotify</button></a>", unsafe_allow_html=True)
            
            # No need for manual code entry - we'll catch it in the callback
            st.write("You'll be redirected back to this app automatically after authorization.")
            return None
        
        if token_info:
            return spotipy.Spotify(auth=token_info['access_token'])
    
    except Exception as e:
        st.error(f"Error connecting to Spotify: {e}")
        return None
    
# Main app function
def main():
    sp = st.session_state.sp if 'sp' in st.session_state else connect_to_spotify()
    
    if sp:
        st.success("Successfully connected to Spotify!")
        
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
            
        # Display playlists
        #elif selection == "Playlists":
        #    display_playlists(sp)
        
        # Display followed artists
        #elif selection == "Following":
        #    display_following(sp)

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