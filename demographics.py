import streamlit as st
from datetime import datetime
#from db_utils import save_to_mongodb

def display_demographics_form():
    """Display demographics survey form and collect responses."""
    st.header("Demographics")

    # Create form for collecting demographic data
    with st.form(key="demographics_form"):
        # Age range selection
        age_range = st.selectbox(
            "Age Range",
            options=[
                "Prefer not to say",
                "18-26", 
                "27-36", 
                "37-50", 
                "Over 50"
            ],
            index=0,
            placeholder="Select your age range"
        )
        
        # Gender selection
        gender = st.selectbox(
            "Gender",
            options=[
                "Prefer not to say",
                "Male", 
                "Female"
            ],
            index=0,
            placeholder="Select your gender"
        )
        
        # Custom gender input if "Other" is selected
        if gender == "Other":
            gender_custom = st.text_input("Please specify:")
            if gender_custom:
                gender = gender_custom
        
        # Location information
        country = st.selectbox(
            "Country",
            options=[
                "Prefer not to say",
                "Italy", "United States", "Canada", "United Kingdom", "Australia", 
                "Germany", "France", "Spain",  "Brazil", "Mexico",
                "Japan", "China", "India", "South Korea", "Other"
            ],
            index=0,
            placeholder="Select your country"
        )
        
        if country == "Other":
            country_custom = st.text_input("Please specify your country:")
            if country_custom:
                country = country_custom
        
        
        # Education level
        education = st.selectbox(
            "Highest Level of Education",
            options=[
                "Prefer not to say",
                "No degree",
                "High School Degree",
                "Bachelor's Degree",
                "Master's Degree",
                "PhD",
            ],
            index=0,
            placeholder="Select your education level"
        )
        
        # Occupation field
        occupation = st.selectbox(
            "Occupation",
            options=[
                "Prefer not to say",
                "Unemployed",
                "Student",
                "Employee",
                "Self-employed",
                "Homemaker",
                "Retired",
            ],
            index=0,
            placeholder="Select your occupation"
        )
        
        
        # Music background
        music_background = st.multiselect(
            "Music Background:",
            options=[
                "Prefer not to say",
                "I play an instrument",
                "I have formal music education",
                "I work in the music industry",
                "I'm a casual listener",
                "Music is an important part of my daily life",
                "I attend concerts/festivals regularly",
                "I create/produce music"
            ],
            placeholder="Select all that apply"
        )

        # spotify premium
        premium=st.selectbox(
            "Do you have the premium version of spotify?",
            options=[
                "Prefer not to say",
                "Yes",
                "No",
                "I don't know"
            ],
        )

        # payment for spotify
        payed=st.selectbox(
            "Do you pay for the premium version of spotify?",
            options=[
                "Prefer not to say",
                "Yes",
                "No",
                "I don't know"
            ],
        )

        device = st.selectbox(
            "What is the device you listen to music on the most?",
            options=[
                "Prefer not to say",
                "Smartphone",
                "Computer",
                "Tablet",
                "Smart speaker (e.g., Amazon Echo)",
                "Car stereo",
                "Other"
            ],
        )

        listening_moments = st.multiselect(
            "You listen to music while:",
            options=[
                "Prefer not to say",
                "Studying",
                "Working",
                "Traveling",
                "Driving",
                "Relaxing"
            ],
            placeholder="Select all that apply"
        )
        
        # Listening habits
        listening_hours = st.slider(
            "Average hours spent listening to music daily:",
            min_value=0, 
            max_value=12, 
            value=2,
            step=1
        )
        
        # Form submission button
        submitted = st.form_submit_button("Submit Demographics")
        
        if submitted:
            # Compile demographic data
            demographic_data = {
                "age_range": age_range,
                "gender": gender,
                "country": country,
                "education": education,
                "occupation": occupation,
                "music_background": music_background,
                "premium": premium,
                "payed": payed,
                "listening_moments": listening_moments,
                "device": device,

                "listening_hours": listening_hours,
                "submission_timestamp": datetime.now()
            }
            
            # Save to database immediately
            if save_demographics(demographic_data):
                st.session_state.demographics_completed = True
                st.session_state.demographic_data = demographic_data
                st.success("Demographics information saved successfully!")
                st.rerun()
            return demographic_data
    
    return None

def save_demographics(demographic_data):
    """Save demographic data to MongoDB."""
    if not demographic_data:
        return False
    
    # Use the new upsert function
    try:
        from db_utils import upsert_user_document  # Import from your new file
        upsert_user_document('demographics', demographic_data)
        return True
    except Exception as e:
        st.error(f"Error saving demographic data: {str(e)}")
        return False

def main():
    """Main function for demographics survey."""
    
    # Check if demographics were already collected
    if 'demographics_completed' in st.session_state and st.session_state.demographics_completed:
        return True
    
    # Display the form and collect responses
    demographic_data = display_demographics_form()
    
    if demographic_data:
        # Save to database
        save_success = save_demographics(demographic_data)
        if save_success:
            st.session_state.demographics_completed = True
            st.session_state.demographic_data = demographic_data
            return True
    
    return False

if __name__ == "__main__":
    main()