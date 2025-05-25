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
        Our goal is to explore the connection between personality traits and musical preferences.
        """)
        
        # How it works section
        st.subheader("How does it work?")
        st.markdown("""
        1. Connect your Spotify account
        2. Provide a few personal details
        3. Answer some questions about your personality
        4. View a visual representation of your Big Five personality traits alongside your Spotify data
        """)
        
        # Privacy Notice Section
        st.subheader("Privacy & Data Protection:")
        st.markdown("""
        We respect your privacy. All data collected is completely anonymous and we cannot identify who you are from the data. 
        Your responses are used solely for academic research purposes. No personal identifying information is stored or shared, 
        and you can withdraw from the study at any time.
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