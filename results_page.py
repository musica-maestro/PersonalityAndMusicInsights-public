import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from survey import calculate_scores

# Custom CSS for enhanced styling
def local_css():
    st.markdown("""
    <style>
    /* Global Styling */
    .stApp {
        background-color: #f0f2f6;
        font-family: 'Inter', sans-serif;
    }
    
    /* Header Styling */
    h1, h2, h3 {
        color: #2c3e50;
        font-weight: 700;
    }
    
    /* Card Styling */
    .trait-card {
        background-color: white;
        border-radius: 15px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        padding: 20px;
        margin-bottom: 20px;
        transition: transform 0.3s ease;
    }
    
    .trait-card:hover {
        transform: scale(1.03);
    }
    
    /* Metric Styling */
    .stMetric {
        background-color: white;
        border-radius: 10px;
        padding: 15px;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
    }
    
    /* Spotify Section Styling */
    .spotify-card {
        background-color: #1DB954;
        color: white;
        border-radius: 15px;
        padding: 20px;
        margin-bottom: 20px;
    }
    
    /* Divider Styling */
    hr {
        border: 0;
        height: 2px;
        background: linear-gradient(to right, transparent, #2c3e50, transparent);
        margin: 30px 0;
    }
    
    /* Button Styling */
    .stButton > button {
        background-color: #3498db;
        color: white;
        border-radius: 10px;
        border: none;
        padding: 10px 20px;
        transition: background-color 0.3s ease;
    }
    
    .stButton > button:hover {
        background-color: #2980b9;
    }
    </style>
    """, unsafe_allow_html=True)

def main():
    """
    Display integrated results page with Big Five personality results and Spotify data,
    all on a single page without tabs.
    """
    # Apply custom CSS
    local_css()
    
    # Add custom Google Fonts
    st.markdown("""
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;700&display=swap" rel="stylesheet">
    """, unsafe_allow_html=True)
    
    # Animated header with gradient
    st.markdown("""
    <div style="background: linear-gradient(45deg, #3498db, #2c3e50); 
                padding: 30px; 
                border-radius: 15px; 
                text-align: center; 
                margin-bottom: 20px;">
        <h1 style="color: white; font-size: 2.5em; margin-bottom: 10px;">
            🎵 Your Personality & Music Profile 🧠
        </h1>
        <p style="color: #ecf0f1; font-size: 1.1em;">
            Discover the unique connection between your personality and musical taste
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Check if both data types are available
    if 'score_results' not in st.session_state or not st.session_state.spotify_data_collected:
        st.warning("Please complete both the personality survey and Spotify data collection to view your integrated results.")
        return
    
    # Display all sections one after another
    display_big5_results(st.session_state.score_results)
    st.markdown("---")  # Add horizontal divider
    display_spotify_insights()
    st.markdown("---")  # Add horizontal divider
    #display_combined_insights()

def display_big5_results(scores):
    """
    Display Big Five personality results with enhanced styling in 3 columns.
    """
    st.header("Your Big Five Personality Profile")
    
    # Create three columns for the Big Five display with equal spacing
    col1, col2, col3 = st.columns([1, 1, 1])
    
    # Column 1: Numerical Scores
    with col1:
        st.subheader("Your Scores")
        # Display the scores in a metrics container with gradient
        st.markdown("""
        <div style="background: linear-gradient(135deg, #f6d365 0%, #fda085 100%); 
                    border-radius: 15px; 
                    padding: 20px;">
        """, unsafe_allow_html=True)
        
        # Metrics for each trait
        for trait, score in scores.items():
            st.metric(trait, f"{score:.2f}/5")
            #st.metric(trait[:12], f"{score:.2f}/5")  # Truncate long trait names
        
        st.markdown("</div>", unsafe_allow_html=True)
    
    # Column 2: Visual Profile (Radar Chart) - Center Column
    with col2:
        st.subheader("Visual Profile")
        # Create a radar chart with improved styling
        plt.rcParams.update({
            'axes.facecolor': '#f0f2f6',
            'figure.facecolor': '#f0f2f6',
            'font.size': 8,
            'axes.labelcolor': '#2c3e50',
            'xtick.color': '#2c3e50',
            'ytick.color': '#2c3e50'
        })
        
        fig = plt.figure(figsize=(8, 8), facecolor='#f0f2f6')
        ax = fig.add_subplot(111, polar=True)
        
        # Get the traits and scores
        traits = list(scores.keys())
        stats = list(scores.values())

        # Number of variables
        N = len(traits)
        
        # What will be the angle of each axis in the plot
        angles = [n / float(N) * 2 * np.pi for n in range(N)]
        angles += angles[:1]  # Close the loop
        
        # Add the first score again to close the circular graph
        stats += stats[:1]
        
        # Custom color palette
        colors = ['#3498db', '#2ecc71', '#e74c3c', '#f39c12', '#9b59b6']
        
        # Draw the polygon and fill it
        ax.fill(angles, stats, color=colors[0], alpha=0.25)
        ax.plot(angles, stats, linewidth=2, linestyle='solid', color=colors[0])
        
        # Set the angle for each trait
        ax.set_xticks(angles[:-1])
        ax.set_xticklabels(traits, size=10, color='#2c3e50', weight='bold')
        
        # Set y-limits
        ax.set_ylim(0, 5)
        ax.set_facecolor('none')  # Transparent background
        
        # Add title
        plt.title('Big Five Traits', size=12, color='#2c3e50', weight='bold', pad=20)
        
        # Display the chart
        st.pyplot(fig)
    
    # Column 3: Understanding Your Results
    with col3:
        st.subheader("Understanding Your Results")
        
        trait_descriptions = {
            "Extraversion": "Social Energy & Interaction: Reveals how you connect with the world and interact with others.",
            "Agreeableness": "Interpersonal Harmony: Reflects your approach to relationships and social interactions.",
            "Conscientiousness": "Personal Organization: Indicates your approach to planning, responsibility, and goal-setting.",
            "Neuroticism": "Emotional Resilience: Shows how you experience and manage emotional responses.",
            "Openness": "Intellectual Curiosity: Demonstrates your openness to new experiences and creativity."
        }
        
        # Colors for each trait
        trait_colors = {
            "Extraversion": "#3498db",    # Bright Blue
            "Agreeableness": "#2ecc71",   # Emerald Green
            "Conscientiousness": "#e74c3c", # Vibrant Red
            "Neuroticism": "#f39c12",     # Warm Orange
            "Openness": "#9b59b6"         # Purple
        }
        
        # Display trait cards vertically in the third column
        for trait, description in trait_descriptions.items():
            score = scores[trait]
            color = trait_colors[trait]
            
            # Determine text based on score
            if score > 3.5:
                score_text = f"You are **high** in {trait}."
            elif score < 2.5:
                score_text = f"You are **low** in {trait}."
            else:
                score_text = f"You are **moderate** in {trait}."
            
            # Create compact cards for the column layout
            st.markdown(f"""
            <div style="background-color: {color}; 
                        color: white; 
                        padding: 12px; 
                        border-radius: 8px; 
                        margin-bottom: 12px;">
                <h4 style="color: white; margin-bottom: 8px; font-size: 1em;">{trait}</h4>
                <p style="margin-bottom: 8px; font-size: 0.85em;">{description}</p>
                <div style="background-color: rgba(255,255,255,0.2); 
                            padding: 6px; 
                            border-radius: 5px; 
                            text-align: center;
                            font-size: 0.8em;">
                    {score_text.replace('**', '<strong>').replace('**', '</strong>')}
                </div>
            </div>
            """, unsafe_allow_html=True)

def display_spotify_insights():
    """
    Display Spotify insights with enhanced visual design.
    """
    st.header("Your Music Profile 🎧")
    
    # Check if Spotify API connection exists
    if 'sp' not in st.session_state:
        st.warning("Spotify connection not available.")
        return
    
    # Get Spotify connection
    sp = st.session_state.sp
    
    # Top Tracks Section
    st.markdown("""
    <div class="spotify-card">
        <h2 style="color: white; margin-bottom: 15px;">🔥 Your Top 10 Tracks</h2>
        <p style="color: #e0e0e0;">Discover the songs that define your recent musical journey</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Display top tracks (short term)
    try:
        top_tracks = sp.current_user_top_tracks(limit=10, time_range="medium_term")
        
        if not top_tracks['items']:
            st.info("No top tracks found for this time period.")
        else:
            # Display tracks in a grid (2 columns)
            cols = st.columns(2)
            for i, track in enumerate(top_tracks['items']):
                artists = ", ".join([artist['name'] for artist in track['artists']])
                album = track['album']['name']
                preview_url = track['preview_url']
                track_url = track['external_urls']['spotify']
                image_url = track['album']['images'][0]['url'] if track['album']['images'] else None
                
                with cols[i % 2]:
                    st.markdown(f"""
                    <div class="trait-card" style="background-color: white; display: flex; align-items: center;">
                        <img src="{image_url}" style="width: 100px; height: 100px; object-fit: cover; border-radius: 10px; margin-right: 15px;">
                        <div>
                            <h4 style="margin-bottom: 5px;">{track['name']}</h4>
                            <p style="color: #7f8c8d; margin-bottom: 5px;">by {artists}</p>
                            <p style="color: #7f8c8d; margin-bottom: 10px;">Album: {album}</p>
                            <a href="{track_url}" target="_blank" style="background-color: #1DB954; color: white; padding: 5px 10px; border-radius: 5px; text-decoration: none;">
                                Open in Spotify
                            </a>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    if preview_url:
                        st.audio(preview_url)
    except Exception as e:
        st.error(f"Error fetching top tracks: {e}")
    
    # Top Artists Section
    st.markdown("""
    <div class="spotify-card">
        <h2 style="color: white; margin-bottom: 15px;">🌟 Your Top 10 Artists</h2>
        <p style="color: #e0e0e0;">The musical talents that resonate with your soul</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Display top artists (short term)
    try:
        top_artists = sp.current_user_top_artists(limit=10, time_range="medium_term")
        
        if not top_artists['items']:
            st.info("No top artists found for this time period.")
        else:
            # Display artists in a grid (2 columns)
            cols = st.columns(2)
            for i, artist in enumerate(top_artists['items']):
                genres = ", ".join(artist['genres'][:3]) if artist['genres'] else "Not specified"
                image_url = artist['images'][0]['url'] if artist['images'] else None
                artist_url = artist['external_urls']['spotify']
                
                with cols[i % 2]:
                    st.markdown(f"""
                    <div class="trait-card" style="background-color: white; display: flex; align-items: center;">
                        <img src="{image_url}" style="width: 100px; height: 100px; object-fit: cover; border-radius: 10px; margin-right: 15px;">
                        <div>
                            <h4 style="margin-bottom: 5px;">{artist['name']}</h4>
                            <p style="color: #7f8c8d; margin-bottom: 5px;">Genres: {genres}</p>
                            <p style="color: #7f8c8d; margin-bottom: 10px;">Popularity: {artist['popularity']}/100</p>
                            <a href="{artist_url}" target="_blank" style="background-color: #1DB954; color: white; padding: 5px 10px; border-radius: 5px; text-decoration: none;">
                                Open in Spotify
                            </a>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
    except Exception as e:
        st.error(f"Error fetching top artists: {e}")

    # Genre Insights Section - Enhanced Version
    st.markdown("""
    <div class="spotify-card">
        <h2 style="color: white; margin-bottom: 15px;">🎼 Your Music Genre Landscape</h2>
        <p style="color: #e0e0e0;">Explore the musical genres that define your taste</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Get top genres
    try:
        top_artists = sp.current_user_top_artists(limit=50, time_range="medium_term")
        all_genres = []
        for artist in top_artists['items']:
            all_genres.extend(artist['genres'])
        
        # Count genre occurrences
        genre_counts = {}
        for genre in all_genres:
            if genre in genre_counts:
                genre_counts[genre] += 1
            else:
                genre_counts[genre] = 1
        
        # Sort genres by count (highest to lowest - most listened at top)
        top_genres = sorted(genre_counts.items(), key=lambda x: x[1], reverse=True)[:8]
        
        # Create a beautiful enhanced bar chart for genres
        if top_genres:
            # Set up the figure with better styling
            fig, ax = plt.subplots(figsize=(12, 8))
            fig.patch.set_facecolor('#f0f2f6')
            ax.set_facecolor('#ffffff')
            
            # Prepare data (reverse order so highest is at top)
            genre_names = [genre.replace('-', ' ').title() for genre, _ in reversed(top_genres)]
            genre_values = [count for _, count in reversed(top_genres)]
            
            # Create a beautiful gradient color palette
            colors = ['#1DB954', '#1ed760', '#2ecc71', '#3498db', '#9b59b6', '#e74c3c', '#f39c12', '#34495e']
            
            # Create horizontal bar chart
            bars = ax.barh(range(len(genre_names)), genre_values, 
                          color=colors[:len(genre_names)], 
                          height=0.7,
                          edgecolor='white',
                          linewidth=2)
            
            # Add value labels on bars
            for i, (bar, value) in enumerate(zip(bars, genre_values)):
                width = bar.get_width()
                ax.text(width + 0.1, bar.get_y() + bar.get_height()/2, 
                       f'{value}', ha='left', va='center', 
                       fontweight='bold', fontsize=12, color='#2c3e50')
            
            # Customize the chart
            ax.set_yticks(range(len(genre_names)))
            ax.set_yticklabels(genre_names, fontsize=12, fontweight='bold', color='#2c3e50')
            ax.set_xlabel('Number of Artists', fontsize=14, fontweight='bold', color='#2c3e50')
            ax.set_title('Your Musical Genre Spectrum', fontsize=18, fontweight='bold', 
                        color='#2c3e50', pad=20)
            
            # Remove top and right spines
            ax.spines['top'].set_visible(False)
            ax.spines['right'].set_visible(False)
            ax.spines['left'].set_linewidth(2)
            ax.spines['bottom'].set_linewidth(2)
            
            # Add grid for better readability
            ax.grid(axis='x', alpha=0.3, linestyle='--', linewidth=1)
            ax.set_axisbelow(True)
            
            # Set x-axis limits with some padding
            ax.set_xlim(0, max(genre_values) * 1.15)
            
            # Tight layout to ensure everything fits
            plt.tight_layout()
            
            # Display the chart
            st.pyplot(fig)
            
            # Add some insights below the chart
            st.markdown(f"""
            <div style="background-color: white; 
                        border-radius: 15px; 
                        padding: 20px; 
                        margin-top: 20px;
                        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);">
                <h3 style="color: #2c3e50; margin-bottom: 15px;">🎯 Your Music Insights</h3>
                <ul style="color: #34495e; list-style-type: none; padding-left: 0;">
                    <li style="margin-bottom: 10px;">
                        <strong>🥇 Primary Genre:</strong> <span style="color: #1DB954; font-weight: bold;">{top_genres[0][0].replace('-', ' ').title()}</span> 
                        ({top_genres[0][1]} artists)
                    </li>
                    <li style="margin-bottom: 10px;">
                        <strong>🎵 Total Genres:</strong> {len(genre_counts)} unique genres discovered
                    </li>
                    <li style="margin-bottom: 10px;">
                        <strong>🌟 Diversity Score:</strong> 
                        {"High" if len(genre_counts) > 15 else "Medium" if len(genre_counts) > 8 else "Focused"} 
                        musical diversity
                    </li>
                </ul>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.write("No genre data available.")
                
    except Exception as e:
        st.error(f"Error generating genre insights: {e}")

if __name__ == "__main__":
    main()