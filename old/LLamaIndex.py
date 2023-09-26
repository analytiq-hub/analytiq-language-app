from dotenv import load_dotenv
import os
import sys
import logging
import shutil
import datetime

import streamlit as st

from llama_index import VectorStoreIndex, ServiceContext
from llama_index.llms import OpenAI
from llama_index import SimpleDirectoryReader
from llama_index import StorageContext, load_index_from_storage
import openai

import utils

# Global variables
SYSTEM_PROMPT_DEFAULT = """You are a helpful assistant. You do not respond as 'User' or pretend to be 'User'. You only respond once as Assistant."""

# Initialize the page
utils.page_init()

# Enable logging only once. Ensure re-runs of the file don't result in duplicate logs.
# Set log level to INFO for saner output.
if 'logging_initialized' not in st.session_state:
    logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)
    logging.getLogger().addHandler(logging.StreamHandler(stream=sys.stdout))
    st.session_state['logging_initialized'] = True

# This should be first streamlit command called
st.set_page_config(page_title="LLamaIndex Ask The Documents")
st.title("LLamaIndex Ask The Documents")

# Set up the page header
utils.page_header()

model_chunk_size = {
    "gpt-3.5-turbo": 1500,
    "gpt-3.5-turbo-16k": 6000, 
    "gpt-4": 3000, 
    "gpt-4-32k": 32000,
}

# Model selection
model = st.sidebar.selectbox("Choose a model:", 
                             ["gpt-4", 
                              "gpt-4-32k",
                              "gpt-3.5-turbo", 
                              "gpt-3.5-turbo-16k"], 
                              key="model")

# Model hyper parameters
st.session_state['temperature'] = st.sidebar.slider('Temperature:', 
                                                    min_value=0.01, 
                                                    max_value=5.0, 
                                                    value=0.5, 
                                                    step=0.01)

system_prompt = st.sidebar.text_area('Prompt before the chat starts. Edit here if desired:', SYSTEM_PROMPT_DEFAULT, height=60)
if system_prompt != SYSTEM_PROMPT_DEFAULT and system_prompt not in [None, ""]:
    st.session_state['system_prompt'] = system_prompt + "\n\n"
else:
    st.session_state['system_prompt'] = SYSTEM_PROMPT_DEFAULT

# Add the "Clear Chat History" button to the sidebar
clear_chat_history_button = st.sidebar.button("Clear Chat History")
clear_db = st.sidebar.button("Reload Data")

def reset_chat_messages():
    """Reset the chat messages history"""
    st.session_state.messages = [
        {"role": "assistant", "content": "Ask me a question about Lexington local government!"}
    ]

# Check if the button is clicked
if clear_chat_history_button:
    reset_chat_messages()

if "messages" not in st.session_state.keys(): 
    # Initialize the chat messages history
    reset_chat_messages()

def index_data():
    """
    Load the documents from the data directory and index them.
    Set the dummy_arg to the current time to force a re-run of this function.
    """
    with st.spinner(text="Indexing docs – hang tight! This should take 1-2 minutes."):
        reader = SimpleDirectoryReader(input_dir="./data", recursive=True)
        docs = reader.load_data()
        st.write(f"Loaded {len(docs)} document fragments.")
        llm = OpenAI(model=model, 
                     temperature=st.session_state['temperature'], 
                     system_prompt=st.session_state['system_prompt'])
        service_context = ServiceContext.from_defaults(llm=llm)
        index = VectorStoreIndex.from_documents(docs, service_context=service_context)
        return index
    
@st.cache_resource(show_spinner=False)
def index_data_cached():
    return index_data()

def save_index(index):
    """Save the index to the storage directory"""
    index.storage_context.persist()

def load_index():
    """Load the index from the storage directory"""
    if not os.path.exists("./storage/docstore.json"):
        index = index_data()
        save_index(index)
        return index
    
    with st.spinner(text="Loading index from disk."):
        # rebuild storage context
        storage_context = StorageContext.from_defaults(persist_dir="./storage")
        # load index
        index = load_index_from_storage(storage_context)
        return index

@st.cache_resource(show_spinner=False)
def load_index_cached():
    return load_index()

index = None

# Clear the document database
if clear_db or not os.path.exists("./storage"):
    # Remove recursively the files under the storage directory
    shutil.rmtree("./storage", ignore_errors=True)
    # Re-create the storage directory
    os.makedirs("./storage", exist_ok=True)

    index = index_data()
    save_index(index)

if index is None:
    index = load_index_cached()
chat_engine = index.as_chat_engine(chat_mode="best", verbose=True)

if prompt := st.chat_input("Your question"): # Prompt for user input and save to chat history
    st.session_state.messages.append({"role": "user", "content": prompt})

for message in st.session_state.messages: # Display the prior chat messages
    with st.chat_message(message["role"]):
        st.write(message["content"])

# If last message is not from assistant, generate a new response
if st.session_state.messages[-1]["role"] != "assistant":
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            response = chat_engine.chat(prompt)
            st.write(response.response)
            message = {"role": "assistant", "content": response.response}
            st.session_state.messages.append(message) # Add response to message history


# Set up the page footer
utils.page_footer()