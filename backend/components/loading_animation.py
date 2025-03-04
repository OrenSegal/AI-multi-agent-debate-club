import streamlit as st
import time
import random

def display_debate_preparation_screen(topic):
    """
    Display an engaging animation showing debate preparation.
    This visualizes the AI 'thinking' process before the debate starts.
    """
    # Create containers
    title = st.empty()
    animation = st.empty()
    progress = st.empty()
    
    # Show preparation phases
    phases = [
        "Researching background information...",
        "Analyzing key arguments...",
        "Evaluating historical debates on this topic...",
        "Identifying supporting evidence...",
        "Formulating opening statements...",
        "Preparing counter-arguments...",
        "Planning debate strategy..."
    ]
    
    title.markdown(f"## Preparing debate on: {topic}")
    
    for phase in phases:
        # Display current phase
        animation.info(phase)
        
        # Show a 'thinking' animation
        thinking = ""
        for i in range(3):
            for dots in range(4):
                thinking = "." * dots
                progress.markdown(f"**AI thinking{thinking}**")
                time.sleep(0.3)
            
        # 50% chance of showing a relevant fact for this phase
        if random.random() > 0.5:
            facts = {
                "Researching background information...": 
                    "AI models like this one process thousands of documents in seconds to gather relevant information.",
                "Analyzing key arguments...": 
                    "Critical thinking involves evaluating arguments for logical consistency, evidence quality, and assumptions.",
                "Evaluating historical debates on this topic...": 
                    "Historical context helps identify how perspectives on this topic have evolved over time.",
                "Identifying supporting evidence...": 
                    "Strong debates use a combination of statistical data, expert opinions, and real-world examples.",
                "Formulating opening statements...": 
                    "A good opening statement clearly states a position and previews key arguments.",
                "Preparing counter-arguments...": 
                    "Anticipating opposing viewpoints is a crucial debate strategy.",
                "Planning debate strategy...": 
                    "The Greek philosopher Aristotle identified three persuasive appeals: ethos (credibility), pathos (emotion), and logos (logic)."
            }
            progress.markdown(f"**Fun fact:** {facts.get(phase, 'Debate preparation is a sophisticated process!')}")
            time.sleep(2)
    
    # Final message
    animation.success("Debate preparation complete! Starting momentarily...")
    progress.empty()
    time.sleep(1)
    
    # Clear all temporary elements
    title.empty()
    animation.empty()

# For testing directly
if __name__ == "__main__":
    st.set_page_config(page_title="Debate Preparation", layout="wide")
    display_debate_preparation_screen("Should artificial intelligence be regulated?")