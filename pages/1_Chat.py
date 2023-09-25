import streamlit as st
from langchain.chat_models import ChatOpenAI
from langchain.memory import ConversationBufferMemory
from langchain.callbacks.base import BaseCallbackHandler
from langchain.callbacks import get_openai_callback
from langchain.chains import ConversationalRetrievalChain

import utils
from config_utils import (
    get_analytiq_config,
    get_categories,
    get_collections,
)
from chroma_utils import (
    get_chroma_retriever
)

# Initialize the page
utils.page_init()

# This should be first streamlit command called
st.set_page_config(page_title="Chat With Lexington Public Records")
st.title("Chat With Lexington Public Records")

# Set up the page header
utils.page_header()

# Get the configuration
analytiq_config = get_analytiq_config()
# Get the categories
analytiq_categories = get_categories(analytiq_config=analytiq_config)
# Get the collections
analytiq_collections = get_collections(analytiq_config=analytiq_config)

# Sidebar menu setup
clear_message_history_p = st.sidebar.button("Clear message history")

# Create multiple choice dropdown button
document_type = st.sidebar.multiselect(
    label="Document Type:",
    options=analytiq_categories["type"],
    default=[],
    key="document_type",
    help="Select the type of document you want to search for.")

document_year = st.sidebar.multiselect(
    label="Document Year:",
    options=analytiq_categories["year"],
    default=[],
    key="document_year",
    help="Select the year you want to search for.")

# Checkbox for advanced options
advanced_options = st.sidebar.checkbox("Advanced Options", value=False, key="advanced_options")
if advanced_options:
    model = st.sidebar.selectbox("Choose a model:", 
                                ["gpt-4", 
                                "gpt-4-32k",
                                "gpt-3.5-turbo", 
                                "gpt-3.5-turbo-16k"], 
                                key="model",
                                help="Choose a model to use for the chatbot.")
    analytiq_search_k = st.sidebar.slider("Search K", min_value=1, max_value=15, value=10, key="analytiq_search_k",
                                          help="Number of documents to search for.")
    analytiq_fetch_k = st.sidebar.slider("Fetch K", min_value=1, max_value=10, value=4, key="analytiq_fetch_k",
                                         help="Number of documents to fetch.")
    # Get the index of the default collection in the collection dictionary
    default_collection_index = list(analytiq_collections.keys()).index("default")
    analytiq_collection_name = st.sidebar.selectbox("Collection Name",
                                                    options=list(analytiq_collections.keys()),
                                                    index=default_collection_index,
                                                    key="analytiq_collection_name",
                                                    help="Search this collection")
else:
    model = "gpt-4"
    analytiq_search_k = 10
    analytiq_fetch_k = 4
    analytiq_collection_name = "default"

model_chunk_size = {
    "gpt-3.5-turbo": 1500,
    "gpt-3.5-turbo-16k": 6000, 
    "gpt-4": 3000, 
    "gpt-4-32k": 32000,
}

class StreamHandler(BaseCallbackHandler):
    def __init__(self, container: st.delta_generator.DeltaGenerator, initial_text: str = ""):
        self.container = container
        self.text = initial_text

    def on_llm_new_token(self, token: str, **kwargs) -> None:
        self.text += token
        self.container.markdown(self.text)

def display_references(container, documents, response_idx):
    """
    Display the references in a streamlit container.

    Args:
        container (st.delta_generator.DeltaGenerator): The streamlit container.
        documents (list): The list of documents.
    """
    expander = container.expander("References")
    for idx, doc in enumerate(documents):
        file_name = doc.metadata["file_name"]
        id = doc.metadata["uuid"]
        file_path = f"{analytiq_config['docstore']}/doc/{id}/{file_name}"
        # Create download button
        expander.download_button(label=file_name, data=open(file_path, "rb"), key=f"reference_{response_idx}_{idx}")
        # Write the chunk
        expander.markdown(doc.page_content)

class PrintRetrievalHandler(BaseCallbackHandler):
    def __init__(self, container, response_idx):
        self._container = container
        self._response_idx = response_idx

    def on_retriever_start(self, serialized, query, **kwargs):
        pass

    def on_retriever_end(self, documents, **kwargs):
        # Display the references
        display_references(self._container, documents, self._response_idx)
        # Save the documents
        st.session_state.messages.append({"role": "references", "content": documents})

retriever = get_chroma_retriever(
    analytiq_config=analytiq_config,
    collection_name=analytiq_collection_name,
    search_k=analytiq_search_k,
    fetch_k=analytiq_fetch_k)

# Setup memory for contextual conversation
memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True)

# Setup LLM and QA chain
llm = ChatOpenAI(
    model_name=model, temperature=0, streaming=True
)
qa_chain = ConversationalRetrievalChain.from_llm(
    llm, retriever=retriever, memory=memory, verbose=True
)

if "messages" not in st.session_state or clear_message_history_p:
    st.session_state["messages"] = [{"role": "assistant", "content": "How can I help you?"}]

references = None
response_idx = 0 # The index of the message
for msg in st.session_state.messages:
    if msg["role"] == "references":
        references = msg["content"]
    elif msg["role"] == "user":
        st.chat_message(msg["role"]).write(msg["content"])
        # Clear the references
        references = None
    elif msg["role"] == "assistant":
        with st.chat_message(msg["role"]):
            if references is not None:
                display_references(st.container(), references, response_idx)
            st.write(msg["content"])
        response_idx += 1
    else:
        raise ValueError(f"Unknown role: {msg['role']}")

user_query = st.chat_input(placeholder="Ask me anything!")

if user_query:
    st.session_state.messages.append({"role": "user", "content": user_query})
    st.chat_message("user").write(user_query)

    with st.chat_message("assistant"):
        retrieval_handler = PrintRetrievalHandler(st.container(), response_idx)
        stream_handler = StreamHandler(st.empty())

        with get_openai_callback() as cost:
            response = qa_chain.run(user_query, callbacks=[retrieval_handler, stream_handler])
            print(cost)

        st.session_state.messages.append({"role": "assistant", "content": response})

# Set up the page footer
utils.page_footer()