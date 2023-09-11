import os
import json
import streamlit as st


from langchain.embeddings.sentence_transformer import SentenceTransformerEmbeddings
from langchain.vectorstores import Chroma
import chromadb
import uuid
from chromadb.config import Settings

from tqdm import tqdm
from langchain.embeddings.sentence_transformer import SentenceTransformerEmbeddings
from langchain.text_splitter import CharacterTextSplitter
from langchain.document_loaders import DirectoryLoader
from langchain.document_loaders import UnstructuredPDFLoader

import utils
from config_utils import (
    get_analytiq_config,
    get_categories,
    get_docs,
    save_categories,
    save_docs,
    normalize_chroma_schema
)

# Initialize the page
utils.page_init()

# This should be first streamlit command called
st.set_page_config(page_title="Schema")
st.title("Schema")

# Set up the page header
utils.page_header()

# Get the ChromaDB configuration
analytiq_config = get_analytiq_config()
# Get the categories
analytiq_categories = get_categories(analytiq_config=analytiq_config)
# Get the docs
analytiq_docs = get_docs(analytiq_config=analytiq_config)


# Create buttons to normalize the schema
normalize_schema = st.button("Normalize Schema")
if normalize_schema:
    normalize_chroma_schema(analytiq_config=analytiq_config)
    
    # Reload the categories and the docs
    analytiq_categories = get_categories(analytiq_config=analytiq_config)
    analytiq_docs = get_docs(analytiq_config=analytiq_config)

# Set up the page footer
utils.page_footer()