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
st.set_page_config(page_title="Categories", layout="wide")
st.title("Categories")

# Set up the page header
utils.page_header()

# Get the ChromaDB configuration
analytiq_config = get_analytiq_config()
# Get the categories
analytiq_categories = get_categories(analytiq_config=analytiq_config)
# Get the docs
analytiq_docs = get_docs(analytiq_config=analytiq_config)
                
def display_categories():
    """
    Display the categories tab
    """
    #for category in analytiq_categories:
    #    st.text(category)
    #    st.write(analytiq_categories[category])


    for category in analytiq_categories:
        col1, col2, col3 = st.columns(3)

        with col2:
            # Text input for new category
            value = st.text_input(f"Enter a new {category}:")

            # Button to add new category
            if st.button(f"Add {category}"):
                if value and value not in analytiq_categories[category]:
                    analytiq_categories[category].append(value)
                    st.success(f"Added {category}: {value}")
        with col3:
            if len(analytiq_categories[category]) > 0:
                values = analytiq_categories[category].copy()
                selected_values_to_remove = st.multiselect(f"Select {category} to remove:", 
                                                         values)
                
    
                if st.button(f"Remove selected {category}"):
                    for value in selected_values_to_remove:
                        if value in analytiq_categories[category]:
                            # Ensure no files have this category
                            nfiles = 0
                            for file_manifest in analytiq_docs:
                                if file_manifest[category] == value:
                                    st.error(f"Cannot remove {category} {value} because file {file_manifest['file_name']} has this {category}.")
                                    nfiles += 1

                            if nfiles == 0:
                                analytiq_categories[category].remove(value)
                                st.success(f"Removed categories: {', '.join(selected_values_to_remove)}")

            else:
                st.text(f"No {category} to remove")

        with col1:
            st.text(category)
            st.write(analytiq_categories[category])

    # Save the categories if they have changed. This routine checks internally if the categories have changed.
    save_categories(analytiq_config=analytiq_config, categories=analytiq_categories)

display_categories()

# Set up the page footer
utils.page_footer()