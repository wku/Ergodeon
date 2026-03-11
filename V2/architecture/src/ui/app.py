"""
Streamlit UI for Ergodeon Agent System
"""

import streamlit as st
import asyncio
import os
from datetime import datetime

# Set page config
st.set_page_config(
    page_title="Ergodeon Agent System",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Title
st.title("🤖 Ergodeon Agent System")
st.markdown("AI-powered software development agents")

# Sidebar
with st.sidebar:
    st.header("Configuration")
    
    # API Key input
    api_key = st.text_input(
        "OpenAI API Key",
        type="password",
        value=os.getenv("OPENAI_API_KEY", ""),
        help="Enter your OpenAI API key"
    )
    
    # Model selection
    model = st.selectbox(
        "Model",
        ["gpt-4-turbo-preview", "gpt-4", "gpt-3.5-turbo"],
        help="Select LLM model"
    )
    
    # Agent selection
    st.header("Agents")
    agent_type = st.selectbox(
        "Select Agent",
        [
            "Auto (Orchestrator)",
            "General Task Execution",
            "Context Gatherer",
            "Spec Task Execution",
            "Feature Requirements-First",
            "Feature Design-First",
            "Bugfix Workflow",
            "Custom Agent Creator"
        ]
    )
    
    st.divider()
    
    # Stats
    st.header("Stats")
    st.metric("Requests", "0")
    st.metric("Success Rate", "100%")
    st.metric("Avg Time", "0s")

# Main content
tab1, tab2, tab3, tab4 = st.tabs(["💬 Chat", "📋 Specs", "📊 History", "⚙️ Settings"])

with tab1:
    st.header("Chat with Ergodeon")
    
    # Chat history
    if "messages" not in st.session_state:
        st.session_state.messages = []
    
    # Display chat messages
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    
    # Chat input
    if prompt := st.chat_input("What would you like to build?"):
        # Add user message
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # Process with agent (placeholder)
        with st.chat_message("assistant"):
            with st.spinner("🔮 Ergodeon is thinking..."):
                # TODO: Integrate with actual orchestrator
                response = f"I understand you want to: {prompt}\n\nThis is a placeholder response. Integration with the orchestrator is coming soon!"
                st.markdown(response)
        
        st.session_state.messages.append({"role": "assistant", "content": response})

with tab2:
    st.header("Specifications")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("Active Specs")
        
        # Placeholder for specs list
        st.info("No active specs. Create one in the Chat tab!")
        
        # Example spec card
        with st.expander("Example: User Authentication"):
            st.markdown("""
            **Type**: Feature  
            **Workflow**: Requirements-First  
            **Status**: In Progress  
            **Phase**: Design
            
            **Files**:
            - ✅ requirements.md
            - ✅ design.md
            - ⏳ tasks.md
            """)
    
    with col2:
        st.subheader("Quick Actions")
        
        if st.button("➕ New Feature Spec", use_container_width=True):
            st.info("Go to Chat tab and describe your feature")
        
        if st.button("🐛 New Bugfix Spec", use_container_width=True):
            st.info("Go to Chat tab and describe the bug")
        
        if st.button("▶️ Execute Tasks", use_container_width=True):
            st.info("Select a spec first")
        
        if st.button("🔄 Refresh", use_container_width=True):
            st.rerun()

with tab3:
    st.header("Request History")
    
    # Placeholder for history
    st.info("No history yet. Start chatting to see your requests here!")
    
    # Example history table
    st.subheader("Recent Requests")
    
    import pandas as pd
    
    df = pd.DataFrame({
        "Time": ["2024-03-10 10:30", "2024-03-10 10:25"],
        "Request": ["Add user authentication", "Fix login bug"],
        "Agent": ["Feature Requirements-First", "Bugfix Workflow"],
        "Status": ["✅ Complete", "✅ Complete"],
        "Duration": ["45s", "32s"]
    })
    
    st.dataframe(df, use_container_width=True, hide_index=True)

with tab4:
    st.header("Settings")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("General")
        
        max_agents = st.slider("Max Concurrent Agents", 1, 20, 10)
        timeout = st.slider("Agent Timeout (seconds)", 60, 600, 300)
        
        st.subheader("Memory")
        
        memory_limit = st.slider("Memory Entries", 1000, 50000, 10000)
        retention_days = st.slider("Retention Days", 7, 90, 30)
    
    with col2:
        st.subheader("LLM")
        
        temperature = st.slider("Temperature", 0.0, 1.0, 0.7, 0.1)
        max_tokens = st.slider("Max Tokens", 1000, 8000, 4000, 500)
        
        st.subheader("Logging")
        
        log_level = st.selectbox("Log Level", ["DEBUG", "INFO", "WARNING", "ERROR"])
        
    st.divider()
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("💾 Save Settings", use_container_width=True):
            st.success("Settings saved!")
    
    with col2:
        if st.button("🔄 Reset to Defaults", use_container_width=True):
            st.info("Settings reset to defaults")
    
    with col3:
        if st.button("📥 Export Config", use_container_width=True):
            st.download_button(
                "Download config.yaml",
                "# Config placeholder",
                "config.yaml",
                use_container_width=True
            )

# Footer
st.divider()
st.markdown("""
<div style='text-align: center; color: gray;'>
    Ergodeon Agent System v1.0.0 | 
    <a href='https://github.com/wku/Ergodeon.git'>GitHub</a> | 
    <a href='#'>Documentation</a>
</div>
""", unsafe_allow_html=True)
