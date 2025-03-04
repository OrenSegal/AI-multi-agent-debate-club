import streamlit as st
import os
from dotenv import load_dotenv
from backend.agents.streaming_debate_manager import StreamingDebateManager
from config import OPENROUTER_MODEL
import time

# Load environment variables
load_dotenv()

# Page config
st.set_page_config(
    page_title="AI Debate Club",
    page_icon="🎭",
    layout="wide",
)

# Title
st.title("🎭 AI Debate Club")
st.write("Watch AI agents debate topics and learn from their arguments.")

# Initialize session state
if "debate_phases" not in st.session_state:
    st.session_state.debate_phases = []
if "is_debate_complete" not in st.session_state:
    st.session_state.is_debate_complete = False
if "last_update_check" not in st.session_state:
    st.session_state.last_update_check = time.time()
if "showed_animation" not in st.session_state:
    st.session_state.showed_animation = False

# Function to add a new phase
def add_debate_phase(phase):
    # Check if phase already exists
    phase_type = phase.get("type")
    round_num = phase.get("round")
    
    # Skip if this phase already exists
    if any(
        (p.get("type") == phase_type and 
         p.get("round", 0) == round_num)
        for p in st.session_state.debate_phases
    ):
        return False
    
    # Add the new phase
    st.session_state.debate_phases.append(phase)
    return True

# Sidebar for debate setup
with st.sidebar:
    st.header("Debate Settings")
    
    # Topic selection
    topic_options = [
        "Should artificial intelligence development be regulated by governments?",
        "Is universal basic income a viable economic policy?",
        "Should social media platforms be held responsible for content moderation?",
        "Is space exploration a worthwhile investment of resources?",
        "Should genetic engineering of humans be permitted?",
        "Custom topic..."
    ]
    
    selected_topic = st.selectbox("Select a debate topic", topic_options)
    
    if selected_topic == "Custom topic...":
        custom_topic = st.text_input("Enter your custom debate topic:")
        debate_topic = custom_topic if custom_topic else "AI regulation"
    else:
        debate_topic = selected_topic
    
    # Number of rounds
    num_rounds = st.slider("Number of debate rounds", min_value=1, max_value=5, value=2)
    
    # Start debate button
    start_button = st.button("Start Debate")

def format_duration(seconds: float) -> str:
    """Format duration in seconds to human readable string."""
    minutes = int(seconds / 60)
    if minutes < 1:
        return "less than a minute"
    elif minutes == 1:
        return "1 minute"
    else:
        return f"{minutes} minutes"

# Main content area
if start_button or "debate_manager" in st.session_state:
    # Reset if starting a new debate
    if start_button and "debate_manager" in st.session_state:
        st.session_state.debate_phases = []
        st.session_state.is_debate_complete = False
        st.session_state.showed_animation = False
        del st.session_state.debate_manager
    
    # Initialize debate manager if not already done
    if "debate_manager" not in st.session_state:
        if not st.session_state.showed_animation:
            # Show the loading animation first
            from backend.components.loading_animation import display_debate_preparation_screen
            display_debate_preparation_screen(debate_topic)
            st.session_state.showed_animation = True
            
        status_placeholder = st.empty()
        with status_placeholder:
            with st.spinner("Initializing AI debaters..."):
                debate_manager = StreamingDebateManager(
                    topic=debate_topic,
                    model_name=OPENROUTER_MODEL,
                    num_rounds=num_rounds
                )
                st.session_state.debate_manager = debate_manager
                debate_manager.start_debate_async()
    
    # Get debate manager and status
    debate_manager = st.session_state.debate_manager
    status = debate_manager.get_debate_status()
    
    # Show current status
    status_container = st.empty()
    with status_container:
        if status["error"]:
            st.error(f"Error in debate: {status['error']}")
            if st.button("Retry Debate"):
                st.session_state.showed_animation = False
                del st.session_state.debate_manager
                st.rerun()
        else:
            if not status["complete"]:
                phase = status["current_phase"]
                duration = format_duration(status["duration"])
                st.info(f"Debate in progress... ({phase}, running for {duration})")
    
    # Check for updates
    if status["has_updates"]:
        new_updates = debate_manager.get_updates()
        for update in new_updates:
            if add_debate_phase(update):
                st.rerun()

    # Display debate phases
    debate_container = st.container()
    with debate_container:
        if st.session_state.debate_phases:
            st.markdown(f"## Debate Topic: {debate_topic}")
            for phase in st.session_state.debate_phases:
                phase_type = phase.get("type")
                content = phase.get("content", "")
                round_num = phase.get("round")
                
                # Format based on phase type
                if phase_type == "introduction":
                    st.markdown("### Introduction")
                    st.markdown(content)
                    
                elif phase_type == "pro_argument":
                    st.markdown(f"### Round {round_num} - Pro Argument")
                    st.markdown(content)
                    
                elif phase_type == "pro_fact_check":
                    with st.expander("Pro Fact Check", expanded=True):
                        st.markdown(content)
                        
                elif phase_type == "con_argument":
                    st.markdown(f"### Round {round_num} - Con Argument")
                    st.markdown(content)
                    
                elif phase_type == "con_fact_check":
                    with st.expander("Con Fact Check", expanded=True):
                        st.markdown(content)
                        
                elif phase_type == "pro_conclusion":
                    st.markdown("### Pro Conclusion")
                    st.markdown(content)
                    
                elif phase_type == "con_conclusion":
                    st.markdown("### Con Conclusion")
                    st.markdown(content)
                    
                elif phase_type == "evaluation":
                    st.markdown("### Evaluation")
                    st.markdown(content)
                    
                    winner = phase.get("winner")
                    pro_score = phase.get("pro_score", 0)
                    con_score = phase.get("con_score", 0)
                    
                    st.markdown(f"**Winner: {winner}** (Pro: {pro_score}, Con: {con_score})")
        
        # Auto-refresh while debate is running
        if not status["complete"]:
            time.sleep(2)
            st.rerun()
else:
    # Display welcome message
    st.write("Select a debate topic and settings in the sidebar, then click 'Start Debate' to begin.")
    st.info("The debate will show the arguments from both sides across multiple rounds, fact-check statements, and conclude with an evaluation.")
