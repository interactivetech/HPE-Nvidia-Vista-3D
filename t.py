import streamlit as st
import time

st.title("Visually Stunning Process Indicator")

if st.button("Start Process"):
    # The status container begins in the 'running' state
    with st.status("Analyzing data...", expanded=True) as status:
        st.write("Searching for data sources...")
        time.sleep(2)  # Simulate a task
        
        st.write("Fetching raw data...")
        time.sleep(3)  # Another simulated task
        
        st.write("Running complex calculations...")
        time.sleep(5)  # The longest task
        
        status.update(label="Data analysis complete!", state="complete", expanded=False)
        
    st.success("All tasks finished successfully!")
