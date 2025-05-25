import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns

def add_styling():
    st.markdown("""
        <style>
            /* convert radio to list of buttons */
            div[role="radiogroup"] {
                flex-direction: row;
            }
            input[type="radio"] + div {
                background: #E8F4F8 !important;
                color: #2C3E50 !important;
                border-radius: 38px !important;
                padding: 8px 18px !important;
                border: 1px solid #B8D8E8 !important;
            }
            input[type="radio"][tabindex="0"] + div {
                background: #B8D8E8 !important;
                color: #2C3E50 !important;
                border: 1px solid #7FB3D5 !important;
            }
            input[type="radio"][tabindex="0"] + div p {
                color: #2C3E50 !important;
            }
            div[role="radiogroup"] label > div:first-child {
                display: none !important;
            }
            div[role="radiogroup"] label {
                margin-right: 0px !important;
            }
            div[role="radiogroup"] {
                gap: 12px;
            }
        </style>
    """, unsafe_allow_html=True)

def main():
    st.title("Big Five Inventory (BFI) Survey")
    
    # Add the custom styling
    add_styling()
    
    st.write("""
    This survey measures an individual on the Big Five Factors (dimensions) of personality.
    Please indicate how much you agree or disagree with each statement.
    """)
    
    # Define the questions
    questions = [
       "Is talkative",
        "Tends to find fault with others",
        "Does a thorough job",
        "Is depressed, blue",
        "Is original, comes up with new ideas",
        "Is reserved",
        "Is helpful and unselfish with others",
        "Can be somewhat careless",
        "Is relaxed, handles stress well",
        "Is curious about many different things",
        "Is full of energy",
        "Starts quarrels with others",
        "Is a reliable worker",
        "Can be tense",
        "Is ingenious, a deep thinker",
        "Generates a lot of enthusiasm",
        "Has a forgiving nature",
        "Tends to be disorganized",
        "Worries a lot",
        "Has an active imagination",
        "Tends to be quiet",
        "Is generally trusting",
        "Tends to be lazy",
        "Is emotionally stable, not easily upset",
        "Is inventive",
        "Has an assertive personality",
        "Can be cold and aloof",
        "Perseveres until the task is finished",
        "Can be moody",
        "Values artistic, aesthetic experiences",
        "Is sometimes shy, inhibited",
        "Is considerate and kind to almost everyone",
        "Does things efficiently",
        "Remains calm in tense situations",
        "Prefers work that is routine",
        "Is outgoing, sociable",
        "Is sometimes rude to others",
        "Makes plans and follows through with them",
        "Gets nervous easily",
        "Likes to reflect, play with ideas",
        "Has few artistic interests",
        "Likes to cooperate with others",
        "Is easily distracted",
        "Is sophisticated in art, music, or literature"
    ]
    
    # Store questions in session state for access in other modules
    if 'questions' not in st.session_state:
        st.session_state.questions = questions
    
    # Define the scale options
    scale_options = {
        1: "Disagree strongly",
        2: "Disagree a little",
        3: "Neither agree nor disagree",
        4: "Agree a little",
        5: "Agree strongly"
    }
    
    # Initialize session state for responses and current question
    if 'responses' not in st.session_state:
        st.session_state.responses = {}
    
    if 'responses_by_text' not in st.session_state:
        st.session_state.responses_by_text = {}

    if 'current_question' not in st.session_state:
        st.session_state.current_question = 0  # Start at introduction screen
    
    if 'submitted' not in st.session_state:
        st.session_state.submitted = False
    
    # Function to handle response changes
    def on_response_change(question_num):
        key = f"q{question_num}"
        value = st.session_state[key]
        
        # Store response with both numeric key and question text key
        st.session_state.responses[question_num] = value
        
        # Also store with question text as key
        question_text = questions[question_num - 1]
        st.session_state.responses_by_text[question_text] = value
    
    # Function to move to next question
    def next_question():
        current_q_num = st.session_state.current_question
        if current_q_num == 0 or current_q_num in st.session_state.responses:
            st.session_state.current_question += 1
        else:
            st.error("Please answer the current question before proceeding.")
        
    # Function to move to previous question
    def prev_question():
        if st.session_state.current_question > 0:
            st.session_state.current_question -= 1
    
    # Function to submit form
    def submit_form():
        if len(st.session_state.responses) == len(questions):
            st.session_state.submitted = True
            st.session_state.current_question = len(questions) + 1  # Move to results screen
        else:
            st.error(f"Please answer all {len(questions)} questions before submitting.")
    
    # Handle navigation based on current question
    if st.session_state.submitted:
        # Display results
        score_results = calculate_scores(st.session_state.responses)
        display_results(score_results)
            
    elif st.session_state.current_question == 0:
        # Start screen
        st.subheader("Instructions")
        st.write("""
        You'll be presented with statements that may or may not describe you.
        For each statement, indicate how much you agree or disagree with it.
        
        You can navigate through the questions using the 'Next' and 'Previous' buttons.
        You must answer each question before proceeding to the next one.
        """)
        
        st.button("Begin Survey", on_click=next_question)
        
    elif st.session_state.current_question <= len(questions):
        # Display the current question
        question_num = st.session_state.current_question
        question_text = questions[question_num - 1]
        
        # Display question text
        st.subheader("I see myself as someone who...")
        st.markdown(f"### **{question_text}**")
        
        # Get the previous response if it exists
        previous_response = None
        if question_num in st.session_state.responses:
            previous_response = st.session_state.responses[question_num]
        
        # Create the radio buttons with Streamlit's native components
        selected_value = st.radio(
            "",
            options=list(scale_options.keys()),
            format_func=lambda x: f"{x} - {scale_options[x]}",
            index=list(scale_options.keys()).index(previous_response) if previous_response else None,
            horizontal=True,
            key=f"q{question_num}",
            on_change=on_response_change,
            args=(question_num,)
        )
        
        # Navigation buttons in two columns
        col1, col2 = st.columns(2)
        
        with col1:
            if question_num > 1:
                st.button("← Previous", on_click=prev_question, use_container_width=True)
            
        with col2:
            if question_num < len(questions):
                next_button_text = "Next →"
            else:
                next_button_text = "Submit"
                
            if question_num < len(questions):
                st.button(next_button_text, on_click=next_question, use_container_width=True)
            else:
                st.button(next_button_text, on_click=submit_form, use_container_width=True)
    
def calculate_scores(responses):
    # Define scoring keys
    scoring_keys = {
        "Extraversion": [1, (6, True), 11, 16, (21, True), 26, (31, True), 36],
        "Agreeableness": [(2, True), 7, (12, True), 17, 22, (27, True), 32, (37, True), 42],
        "Conscientiousness": [3, (8, True), 13, (18, True), (23, True), 28, 33, 38, (43, True)],
        "Neuroticism": [4, (9, True), 14, 19, (24, True), 29, (34, True), 39],
        "Openness": [5, 10, 15, 20, 25, 30, (35, True), 40, (41, True), 44]
    }
    
    # Calculate scores for each dimension
    scores = {}
    for dimension, items in scoring_keys.items():
        total = 0
        count = 0
        for item in items:
            if isinstance(item, tuple):
                question_num, reverse = item
                # Reverse scoring: 1->5, 2->4, 3->3, 4->2, 5->1
                if reverse and question_num in responses:
                    total += 6 - responses[question_num]
                    count += 1
            else:
                if item in responses:
                    total += responses[item]
                    count += 1
        
        scores[dimension] = total / count if count > 0 else 0  # Calculate average score
    
    return scores

def display_results(scores):
    st.subheader("Your Big Five Personality Results")
    
    # Display the scores using Streamlit's native components
    for trait, score in scores.items():
        st.metric(trait, f"{score:.2f}/5")
    
    # Create a radar chart
    fig = plt.figure(figsize=(10, 8))
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
    
    # Draw the polygon and fill it
    ax.fill(angles, stats, color='skyblue', alpha=0.25)
    ax.plot(angles, stats, linewidth=2, linestyle='solid', color='royalblue')
    
    # Set the angle for each trait
    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(traits, size=12, color='black', weight='bold')
    
    # Set y-limits
    ax.set_ylim(0, 5)
    
    # Add title
    plt.title('Big Five Personality Traits', size=15, color='navy', weight='bold', pad=20)
    
    # Use beautiful styling with seaborn
    sns.set_style("whitegrid")
    
    # Display the chart
    st.pyplot(fig)
    
    # Display trait descriptions using Streamlit's native components
    st.subheader("Understanding Your Results")
    
    trait_descriptions = {
        "Extraversion": """
        **High Score**: Outgoing, sociable, assertive, enthusiastic. Enjoys being with people, full of energy.
        **Low Score**: Reserved, quiet, prefers solitude and one-on-one interactions.
        """,
        
        "Agreeableness": """
        **High Score**: Trusting, helpful, cooperative, sympathetic to others, warm.
        **Low Score**: Critical, uncooperative, suspicious, competitive rather than collaborative.
        """,
        
        "Conscientiousness": """
        **High Score**: Organized, thorough, planful, efficient, responsible, reliable.
        **Low Score**: Spontaneous, disorganized, prefers flexibility over structured plans.
        """,
        
        "Neuroticism": """
        **High Score**: Emotionally reactive, prone to stress, worry, and negative emotions.
        **Low Score**: Emotionally stable, calm under pressure, secure, less easily upset.
        """,
        
        "Openness": """
        **High Score**: Creative, curious, imaginative, prefers variety, open to new experiences.
        **Low Score**: Conventional, practical, prefers routine and the familiar.
        """
    }
    
    for trait, description in trait_descriptions.items():
        score = scores[trait]
        st.markdown(f"### {trait}: {score:.2f}/5")
        st.markdown(description)
        
        # Display interpretation based on score
        if score > 3.5:
            st.info(f"Your score suggests you are **high** in {trait}.")
        elif score < 2.5:
            st.info(f"Your score suggests you are **low** in {trait}.")
        else:
            st.info(f"Your score suggests you are **moderate** in {trait}.")
        
        st.divider()

    st.write("""
    **Note**: This assessment is for informational purposes only and should not be used as a 
    professional psychological evaluation. The Big Five personality traits represent broad domains 
    of personality and there is value in all parts of each spectrum.
    """)

if __name__ == "__main__":
    main()