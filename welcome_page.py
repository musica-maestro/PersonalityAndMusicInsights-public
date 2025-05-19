import streamlit as st

def welcome_page():
    """
    Displays the welcome page for the Rumors Research application.
    Returns nothing, but changes app_state session variable when button is clicked.
    """
    # Create columns for better layout
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        # Header with logo/title
        st.title("Welcome to Personality and Music Insight Research!")
        
        # Main welcome message
        st.markdown("""
        We are a research team from Roma Tre University's AI Research Lab. 
        Our goal is to provide you with personalized movie recommendations based on your preferences.
        """)
        
        # How it works section
        st.subheader("How does it work?")
        st.markdown("""
        1. Access to your spotify account
        2. Answer a few personal questions about yourself
        3. Answer a few questions about your personality
        4. Have a visual of your big5 personality traits and your spotify data
        """)
        
        # Contact information
        st.subheader("For any further question:")
        st.markdown("""
        **Leonardo Recchia**  
        Email: leo.recchia2@stud.uniroma3.it
        """)
        st.markdown("""
        **Alessio Ferrato**  
        Email: alessio.ferrato@uniroma3.it
        """)
        st.markdown("""
        **Giuseppe Sansonetti**  
        Email: giuseppe.sansonetti@uniroma3.it
        """)
        
        # Proceed button - this will change the app state when clicked
        if 'app_state' not in st.session_state:
            st.session_state.app_state = "welcome"
            
        if st.button("Begin Survey", key="start_button", use_container_width=True):
            st.session_state.app_state = "spotify"
            st.rerun()