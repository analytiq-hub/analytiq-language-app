"""
This is a Streamlit chatbot app that includes session chat history.
"""
import streamlit as st

from langchain import OpenAI
from langchain.vectorstores import VectorStore
from langchain.chains import RetrievalQA
from langchain.llms import OpenAI, Replicate
from langchain.callbacks.base import BaseCallbackHandler
import pickle

import replicate
import os
from utils import debounce_replicate_run

import utils

# Initialize the page
utils.page_init()

###Initial UI configuration:###
st.set_page_config(page_title="Airbyte Chatbot by Analytiq", 
                   # page_icon=logo1, # uncomment to add your own logo
                   layout="wide")

# Set up the page header
utils.page_header()

# Update on change
VECTORSTORE_FILE = os.environ.get("VECTORSTORE_FILE", "vectorstore.pkl")
with open(VECTORSTORE_FILE, "rb") as f:
    global vectorstore
    local_vectorstore: VectorStore = pickle.load(f)

###Global variables:###
REPLICATE_API_TOKEN = os.environ.get('REPLICATE_API_TOKEN', default='')
#Your your (Replicate) models' endpoints:
REPLICATE_MODEL_NONE = None
REPLICATE_MODEL_ENDPOINT7B = os.environ.get('REPLICATE_MODEL_ENDPOINT7B', default='')
REPLICATE_MODEL_ENDPOINT13B = os.environ.get('REPLICATE_MODEL_ENDPOINT13B', default='')
REPLICATE_MODEL_ENDPOINT70B = os.environ.get('REPLICATE_MODEL_ENDPOINT70B', default='')
PRE_PROMPT = """You are a helpful, respectful and honest assistant. Always answer as helpfully as possible, while being safe. Your answers should not include any harmful, unethical, racist, sexist, toxic, dangerous, or illegal content. Please ensure that your responses are socially unbiased and positive in nature.

If a question does not make any sense, or is not factually coherent, explain why instead of answering something not correct. If you don't know the answer to a question, please don't share false information.
"""

if not (REPLICATE_API_TOKEN and REPLICATE_MODEL_ENDPOINT13B and REPLICATE_MODEL_ENDPOINT7B):
    st.warning("Add a `.env` file to your app directory with the keys specified in `.env_template` to continue.")
    st.stop()

#container for the chat history
response_container = st.container()
#container for the user's text input
container = st.container()
#Set up/Initialize Session State variables:
if 'chat_dialogue' not in st.session_state:
    st.session_state['chat_dialogue'] = []
if 'llm' not in st.session_state:
    #st.session_state['llm'] = REPLICATE_MODEL_ENDPOINT13B
    st.session_state['llm'] = REPLICATE_MODEL_ENDPOINT70B
if 'temperature' not in st.session_state:
    st.session_state['temperature'] = 0.1
if 'top_p' not in st.session_state:
    st.session_state['top_p'] = 0.9
if 'max_seq_len' not in st.session_state:
    st.session_state['max_seq_len'] = 512
if 'pre_prompt' not in st.session_state:
    st.session_state['pre_prompt'] = PRE_PROMPT
if 'string_dialogue' not in st.session_state:
    st.session_state['string_dialogue'] = ''

#Dropdown menu to select the model edpoint:
selected_option = st.sidebar.selectbox('Choose a model:', 
                                       ['gpt-3.5-turbo', 'gpt-4', 'LLaMA2-70B', 'LLaMA2-13B', 'LLaMA2-7B'], 
                                       key='model')
if selected_option in ['gpt-3.5-turbo', 'gpt-4']:
    st.session_state['llm'] = selected_option
    st.session_state['llm_type'] = 'openai'
elif selected_option == 'LLaMA2-7B':
    st.session_state['llm'] = REPLICATE_MODEL_ENDPOINT7B
    st.session_state['llm_type'] = 'replicate'
elif selected_option == 'LLaMA2-13B':
    st.session_state['llm'] = REPLICATE_MODEL_ENDPOINT13B
    st.session_state['llm_type'] = 'replicate'
else:
    st.session_state['llm'] = REPLICATE_MODEL_ENDPOINT70B
    st.session_state['llm_type'] = 'replicate'

#Model hyper parameters:
st.session_state['temperature'] = st.sidebar.slider('Temperature:', min_value=0.01, max_value=5.0, value=0.1, step=0.01)
st.session_state['top_p'] = st.sidebar.slider('Top P:', min_value=0.01, max_value=1.0, value=0.9, step=0.01)
st.session_state['max_seq_len'] = st.sidebar.slider('Max Sequence Length:', min_value=64, max_value=4096, value=2048, step=8)

NEW_P = st.sidebar.text_area('Prompt before the chat starts. Edit here if desired:', PRE_PROMPT, height=60)
if NEW_P != PRE_PROMPT and NEW_P != "" and NEW_P != None:
    st.session_state['pre_prompt'] = NEW_P + "\n\n"
else:
    st.session_state['pre_prompt'] = PRE_PROMPT


# Add the "Clear Chat History" button to the sidebar
clear_chat_history_button = st.sidebar.button("Clear Chat History")

# Check if the button is clicked
if clear_chat_history_button:
    # Reset the chat history stored in the session state
    st.session_state['chat_dialogue'] = []


class StreamHandler(BaseCallbackHandler):
    def __init__(self, container, initial_text=""):
        self.container = container
        self.text = initial_text

    def on_llm_new_token(self, token: str, **kwargs) -> None:
        self.text += token
        self.container.markdown(self.text)

with st.chat_message("assistant"):
    st.markdown("How can I help you?")

# Display chat messages from history on app rerun
for message in st.session_state.chat_dialogue:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Accept user input
if prompt := st.chat_input("Type your question here"):
    # Add user message to chat history
    st.session_state.chat_dialogue.append({"role": "user", "content": prompt})
    # Display user message in chat message container
    with st.chat_message("user"):
        st.markdown(prompt)
    
    with st.chat_message("assistant"):
        stream_handler = StreamHandler(st.empty())

        if st.session_state['llm_type'] == 'openai':
            llm = OpenAI(model_name=st.session_state['llm'], 
                        streaming=True, callbacks=[stream_handler],
                        temperature=min(st.session_state['temperature'], 1.0))
        elif st.session_state['llm_type'] == 'replicate':
            llm = Replicate(model="a16z-infra/llama13b-v2-chat:df7690f1994d94e96ad9d568eac121aecf50684a0b0963b25a41cc40061269e5",
                            streaming=True, callbacks=[stream_handler],
                            input={"temperature": 0.75, "max_length": 500, "top_p": 1})
        else:
            st.error(f'Invalid LLM type {st.session_state["llm_type"]}')
            st.stop()

        # The LangChain retrieval chain
        qa = RetrievalQA.from_chain_type(llm=llm, 
                                        chain_type="stuff", 
                                        retriever=local_vectorstore.as_retriever())

        message_placeholder = st.empty()
        full_response = ""
        string_dialogue = st.session_state['pre_prompt']
        for dict_message in st.session_state.chat_dialogue:
            if dict_message["role"] == "user":
                string_dialogue = string_dialogue + "User: " + dict_message["content"] + "\n\n"
            else:
                string_dialogue = string_dialogue + "Assistant: " + dict_message["content"] + "\n\n"
        print (string_dialogue)

        llm_type = st.session_state['llm_type']
        if llm_type == 'openai':# or llm_type == 'replicate':
            # OpenAI query:
            full_response = qa.run(string_dialogue + "Assistant: ")

            # The run() method will call the stream_handler on_llm_new_token() method for each new token
            # The stream_handler will append the new token to the text and display it in the container
            # We're under the with st.chat_message("assistant") context manager, so the text 
            # will be displayed in the chat message container

        elif llm_type == 'replicate':
            # Replicate query:
            output = utils.debounce_replicate_run(st.session_state['llm'], 
                                                  string_dialogue + "Assistant: ", 
                                                  st.session_state['max_seq_len'], 
                                                  st.session_state['temperature'], 
                                                  st.session_state['top_p'], 
                                                  REPLICATE_API_TOKEN)
            # output is iterator, so we need to iterate over it to get the full response
            for item in output:
                full_response += item
                message_placeholder.markdown(full_response + "▌")
            message_placeholder.markdown(full_response)
        else:
            st.error(f'Invalid LLM type {llm_type}')
            st.stop()

    # Add assistant response to chat history
    st.session_state.chat_dialogue.append({"role": "assistant", "content": full_response})

# Set up the page footer
utils.page_footer()

