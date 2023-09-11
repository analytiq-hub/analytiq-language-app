import os

import streamlit as st
import pandas as pd
from langchain.chat_models import ChatOpenAI
from langchain.agents import create_pandas_dataframe_agent
from langchain.agents.agent_types import AgentType

import utils

# Initialize the page
utils.page_init()

# This should be first streamlit command called
st.set_page_config(page_title='Ask the Data')
st.title('Ask the Data')

# Set up the page header
utils.page_header()

#st.sidebar.header("Ask the Data")#Left sidebar menu

###Global variables:###
OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY', default='')
REPLICATE_API_TOKEN = os.environ.get('REPLICATE_API_TOKEN', default='')
#Your your (Replicate) models' endpoints:
REPLICATE_MODEL_NONE = None
REPLICATE_MODEL_ENDPOINT7B = os.environ.get('REPLICATE_MODEL_ENDPOINT7B', default='')
REPLICATE_MODEL_ENDPOINT13B = os.environ.get('REPLICATE_MODEL_ENDPOINT13B', default='')
REPLICATE_MODEL_ENDPOINT70B = os.environ.get('REPLICATE_MODEL_ENDPOINT70B', default='')
PRE_PROMPT = "You are a helpful assistant. You do not respond as 'User' or pretend to be 'User'. You only respond once as Assistant."

if not (OPENAI_API_KEY and REPLICATE_API_TOKEN and REPLICATE_MODEL_ENDPOINT13B and REPLICATE_MODEL_ENDPOINT7B):
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
selected_option = st.sidebar.selectbox('Choose a model:', ['ChatGPT 3.5', 'LLaMA2-70B', 'LLaMA2-13B', 'LLaMA2-7B'], key='model')
if selected_option == 'ChatGPT 3.5':
    st.session_state['llm'] = REPLICATE_MODEL_NONE
elif selected_option == 'LLaMA2-7B':
    st.session_state['llm'] = REPLICATE_MODEL_ENDPOINT7B
elif selected_option == 'LLaMA2-13B':
    st.session_state['llm'] = REPLICATE_MODEL_ENDPOINT13B
else:
    st.session_state['llm'] = REPLICATE_MODEL_ENDPOINT70B
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

# Load CSV file
def load_csv(input_csv):
  df = pd.read_csv(input_csv)
  with st.expander('See DataFrame'):
    st.write(df)
  return df

# Generate LLM response
def generate_response(csv_file, input_query):
  llm = ChatOpenAI(model_name='gpt-3.5-turbo-0613', temperature=0.2, openai_api_key=openai_api_key)
  df = load_csv(csv_file)
  # Create Pandas DataFrame Agent
  agent = create_pandas_dataframe_agent(llm, df, verbose=True, agent_type=AgentType.OPENAI_FUNCTIONS)
  # Perform Query using the Agent
  response = agent.run(input_query)
  return st.success(response)

# Input widgets
uploaded_file = st.file_uploader('Upload a CSV file', type=['csv'])
question_list = [
  'How many rows are there?',
  'What is the range of values for MolWt with logS greater than 0?',
  'How many rows have MolLogP value greater than 0.',
  'Other']
query_text = st.selectbox('Select an example query:', question_list, disabled=not uploaded_file)

# Check if OpenAI API key is in the environment
if 'OPENAI_API_KEY' in os.environ:
  openai_api_key = os.environ['OPENAI_API_KEY']
else:
  openai_api_key = st.text_input('OpenAI API Key', type='password', disabled=not (uploaded_file and query_text))

# App logic
if query_text == 'Other':
  query_text = st.text_input('Enter your query:', placeholder = 'Enter query here ...', disabled=not uploaded_file)
if not openai_api_key.startswith('sk-'):
  st.warning('Please enter your OpenAI API key!', icon='⚠')
if openai_api_key.startswith('sk-') and (uploaded_file is not None):
  st.header('Output')
  generate_response(uploaded_file, query_text)

# Set up the page footer
utils.page_footer()