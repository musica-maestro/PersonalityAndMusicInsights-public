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
        
        # Privacy Notice Section
        st.info("🔒 **Privacy & Data Protection**")
        st.markdown("""
        <div style="background-color: #e8f5e8; padding: 15px; border-radius: 8px; border-left: 4px solid #28a745;">
        <strong>We respect your privacy:</strong><br>
        • All data collected is completely anonymous<br>
        • We cannot identify who you are from the data<br>
        • Your responses are used solely for academic research purposes<br>
        • No personal identifying information is stored or shared<br>
        • You can withdraw from the study at any time
        </div>
        """, unsafe_allow_html=True)
        
        # How it works section
        st.subheader("How does it work?")
        st.markdown("""
        1. Connect your Spotify account
        2. Provide a few personal details
        3. Answer some questions about your personality
        4. View a visual representation of your Big Five personality traits alongside your Spotify data
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