import os
import streamlit as st
from pathlib import Path
from langchain.llms.openai import OpenAI
from langchain.agents import create_sql_agent
from langchain.sql_database import SQLDatabase
from langchain.agents.agent_types import AgentType
from langchain.callbacks import StreamlitCallbackHandler
from langchain.agents.agent_toolkits import SQLDatabaseToolkit

import utils

# Initialize the page
utils.page_init()

# This should be first streamlit command called
st.set_page_config(page_title="Ask The SQL DB")
st.title("Ask The SQL DB")

# Set up the page header
utils.page_header()

model = st.sidebar.selectbox("Choose a model:", 
                             ["gpt-4", 
                              "gpt-4-32k",
                              "gpt-3.5-turbo", 
                              "gpt-3.5-turbo-16k"
                              ], 
                              key="model")

# User inputs
radio_opt = [
    "Use the local MySQL db", 
    "Use the local SQLite db",
    "Connect to your SQL db"
    ]
selected_opt = st.sidebar.radio(label="Choose suitable option", options=radio_opt)
if radio_opt.index(selected_opt) == 0:
    db_uri = os.getenv("MYSQL_URI")
elif radio_opt.index(selected_opt) == 1:
    db_filepath = (Path(__file__).parent / "Chinook.db").absolute()
    db_uri = f"sqlite:////{db_filepath}"
elif radio_opt.index(selected_opt) == 2:
    db_uri = st.sidebar.text_input(
        label="Database URI", placeholder="mysql://user:pass@hostname:port/db"
    )
else:
    raise ValueError(f"Invalid option {selected_opt}")


# Check user inputs
if not db_uri:
    st.info("Please enter database URI to connect to your database.")
    st.stop()


# Setup agent
llm = OpenAI(model_name=model, temperature=0, streaming=True)


@st.cache_resource(ttl="2h")
def configure_db(db_uri):
    return SQLDatabase.from_uri(database_uri=db_uri)


db = configure_db(db_uri)

toolkit = SQLDatabaseToolkit(db=db, llm=llm)

agent = create_sql_agent(
    llm=llm,
    toolkit=toolkit,
    verbose=True,
    agent_type=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
)

if "messages" not in st.session_state or st.sidebar.button("Clear message history"):
    st.session_state["messages"] = [{"role": "assistant", "content": "How can I help you?"}]

for msg in st.session_state.messages:
    st.chat_message(msg["role"]).write(msg["content"])

user_query = st.chat_input(placeholder="Ask me anything!")

if user_query:
    st.session_state.messages.append({"role": "user", "content": user_query})
    st.chat_message("user").write(user_query)

    with st.chat_message("assistant"):
        st_cb = StreamlitCallbackHandler(st.container())
        response = agent.run(user_query, callbacks=[st_cb])
        st.session_state.messages.append({"role": "assistant", "content": response})
        st.write(response)

# Set up the page footer
utils.page_footer()