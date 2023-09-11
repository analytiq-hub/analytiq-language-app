from dotenv import load_dotenv
import replicate
import time
import streamlit as st

# Initialize debounce variables
last_call_time = 0
debounce_interval = 2  # Set the debounce interval (in seconds) to your desired value

def debounce_replicate_run(llm, prompt, max_len, temperature, top_p, API_TOKEN):
    global last_call_time
    print("last call time: ", last_call_time)

    # Get the current time
    current_time = time.time()

    # Calculate the time elapsed since the last call
    elapsed_time = current_time - last_call_time

    # Check if the elapsed time is less than the debounce interval
    if elapsed_time < debounce_interval:
        print("Debouncing")
        return "Hello! You are sending requests too fast. Please wait a few seconds before sending another request."


    # Update the last call time to the current time
    last_call_time = time.time()
    
    output = replicate.run(llm, input={"prompt": prompt + "Assistant: ", "max_length": max_len, "temperature": temperature, "top_p": top_p, "repetition_penalty": 1}, api_token=API_TOKEN)
    return output


def page_init():
    """Initialize the page"""

    # Load the environment variables from the top level .env file
    load_dotenv()

def page_header():
    """Common for all page headers"""

    # Reduce font sizes for input text boxes
    custom_css = """
        <style>
            .stTextArea textarea {font-size: 13px;}
            div[data-baseweb="select"] > div {font-size: 13px !important;}
        </style>
    """
    st.markdown(custom_css, unsafe_allow_html=True)

    # Set a cleaner menu, footer & background:
    hide_streamlit_style = """
                <style>
                footer {visibility: hidden;}
                </style>
                """
    # Also include "#MainMenu {visibility: hidden;}" in the <style> 
    # if you want to hide the Streamlit menu    

    st.markdown(hide_streamlit_style, unsafe_allow_html=True)

def page_footer():
    """Common for all page footers"""
    pass
