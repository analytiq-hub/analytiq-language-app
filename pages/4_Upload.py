import os
import json
import streamlit as st


from langchain.embeddings.sentence_transformer import SentenceTransformerEmbeddings
from langchain.vectorstores import Chroma
import uuid

from tqdm import tqdm
from langchain.embeddings.sentence_transformer import SentenceTransformerEmbeddings
from langchain.text_splitter import CharacterTextSplitter
from langchain.document_loaders import DirectoryLoader
from langchain.document_loaders import UnstructuredPDFLoader

import utils
from config_utils import (
    get_analytiq_config,
    get_categories,
    get_collections,
    get_docs,
    save_docs,
)
from collection_utils import (
    get_collection_loader,
    get_collection_splitter
)
from chroma_utils import (
    get_chroma_client,
    get_chroma_collection,
    check_chroma_file,
    add_chroma_file_chunks,
    delete_chroma_file_chunks
)

# Initialize the page
utils.page_init()

# This should be first streamlit command called
st.set_page_config(page_title="Upload Files", layout="wide")
st.title("Upload Files")

# Set up the page header
utils.page_header()

# Get the ChromaDB configuration
analytiq_config = get_analytiq_config()
# Get the categories
analytiq_categories = get_categories(analytiq_config=analytiq_config)
# Get the collections
analytiq_collections = get_collections(analytiq_config=analytiq_config)
# Get the docs
analytiq_docs = get_docs(analytiq_config=analytiq_config)
# Create the chroma client and save it in the session state
get_chroma_client(analytiq_config=analytiq_config, analytiq_collections=analytiq_collections)

# Checkbox for advanced options
advanced_options = st.sidebar.checkbox("Advanced Options", value=False, key="advanced_options")
if advanced_options:
    # Get the index of the default collection in the collection dictionary
    default_collection_index = list(analytiq_collections.keys()).index("default")
    analytiq_collection_name = st.sidebar.selectbox("Collection Name",
                                                    options=list(analytiq_collections.keys()),
                                                    index=default_collection_index,
                                                    key="analytiq_collection_name",
                                                    help="Search this collection")
else:
    analytiq_collection_name = "default"

def display_upload_files():
    """Display the upload tab
    """

    st.write("Upload file. Select the type and year. Select one or more collections.")
    st.write("")
    st.write("")
    st.write("")

    print("")
    print(f"st.session_state start: {st.session_state}")

    # Create columns
    col1, col2, col3 = st.columns(3)

    with col1:
        # Create file upload widget
        uploaded_file = st.file_uploader("Upload Files", accept_multiple_files=False, type=["pdf"])

        file_name = None
        file_path = None
        file_manifest = None

        if uploaded_file is not None:
            # Check if the file is in the docs
            file_name = uploaded_file.name
            for f_manifest in analytiq_docs:
                if f_manifest["file_name"] == file_name:
                    file_manifest = f_manifest
                    file_path = f"{analytiq_config['docstore']}/doc/{file_manifest['uuid']}/{file_name}"
                    break
            
            if "upload_file" not in st.session_state:
                st.session_state.upload_file = file_name
        else:
            if "upload_file" in st.session_state:
                del st.session_state.upload_file
            if "selected_type" in st.session_state:
                del st.session_state.selected_type
            if "selected_year" in st.session_state:
                del st.session_state.selected_year
            if "collections" in st.session_state:
                del st.session_state.collections
            if "file_in_collection" in st.session_state:
                del st.session_state.file_in_collection

    with col2:
        type_options = [""] + analytiq_categories["type"]
        year_options = [""] + analytiq_categories["year"]

        # Get the type index
        type_index = 0
        if "selected_type" in st.session_state and st.session_state.selected_type != "":
            type_index = type_options.index(st.session_state.selected_type)
        elif file_manifest is not None:
            type_index = type_options.index(file_manifest["type"])

        year_index = 0
        if "selected_year" in st.session_state and st.session_state.selected_year != "":
            year_index = year_options.index(st.session_state.selected_year)
        elif file_manifest is not None:
            year_index = year_options.index(file_manifest["year"])

        # Create a dropdown menu for the type
        selected_type = st.selectbox(label="Type:",
                                     options=type_options,
                                     index=type_index,
                                     label_visibility="visible",
                                     key="selected_type")
        # Create a dropdown menu for the year
        selected_year = st.selectbox(label="Year:",
                                     options=year_options,
                                     index=year_index,
                                     label_visibility="visible",
                                     key="selected_year")
    
    with col3:
        checkbox = {}

        # Initialize the collections
        if "collections" not in st.session_state:
            st.session_state.collections = {}
        if "file_in_collection" not in st.session_state:
            st.session_state.file_in_collection = {}

        st.text("Collections:")
        for collection_name in analytiq_collections:
            checkbox_disabled=True
            st.session_state.file_in_collection[collection_name] = False

            if file_manifest is not None:
                # Enable the checkbox
                checkbox_disabled=False

                # Check if the file is in the collection
                file_in_collection = check_chroma_file(analytiq_config=analytiq_config,
                                                       collection_name=collection_name,
                                                       file_manifest=file_manifest)
                st.session_state.file_in_collection[collection_name] = file_in_collection

            checkbox_key = f"checkbox_{collection_name}"
            if checkbox_key not in st.session_state:
                # Initialize the checkbox
                checkbox_state = st.session_state.file_in_collection[collection_name]
            else:
                # Get the checkbox state
                checkbox_state = st.session_state[checkbox_key]

            # Create the checkbox
            checkbox = st.checkbox(label=collection_name, 
                                   value=checkbox_state,
                                   disabled=checkbox_disabled,
                                   key=checkbox_key)

    if uploaded_file is not None:
        bytes_data = uploaded_file.getvalue()

        if selected_type == "" or selected_year == "":
            st.error("Please select a type and a year.")
        elif file_manifest:
            if selected_type != file_manifest["type"] or selected_year != file_manifest["year"]:
                # Update the file manifest. It is a reference to the analytiq_docs, so 
                # analytiq_docs will be updated as well.
                file_manifest["type"] = selected_type
                file_manifest["year"] = selected_year

                # Save the docs
                save_docs(analytiq_config=analytiq_config, docs=analytiq_docs)
        else:
            # Create a uuid for the file
            id = str(uuid.uuid4())
            # Create the uuid folder
            os.makedirs(f"{analytiq_config['docstore']}/doc/{id}", exist_ok=True)
            # Save the file to the uuid folder
            file_path = f"{analytiq_config['docstore']}/doc/{id}/{file_name}"
            with open(file_path, "wb") as f:
                f.write(bytes_data)
                st.info(f"Saved {file_path}")
            
            # Create a file manifest
            file_manifest = {
                "file_name": file_name,
                "type": selected_type,
                "year": selected_year,
                "uuid": id
            }

            # Add the file manifest to the docs
            analytiq_docs.append(file_manifest)

            # Save the docs
            save_docs(analytiq_config=analytiq_config, docs=analytiq_docs)

        # Upload the file to the collections
        for collection_name in analytiq_collections:
            collection = analytiq_collections[collection_name]
            checkbox_key = f"checkbox_{collection_name}"
            checkbox = st.session_state[checkbox_key]
            if not st.session_state.file_in_collection[collection_name] and checkbox:
                # Will upload the file to this collection
                with st.status(f"Parsing {file_name}..."):
                    # Create the pdf loader
                    loader = get_collection_loader(analytiq_config=analytiq_config,
                                                   collection=collection,
                                                   file_path=file_path)
                    docs = loader.load()

                # Split it into chunks
                with st.status(f"Splitting {file_name}..."):
                    splitter = get_collection_splitter(analytiq_config=analytiq_config,
                                                       collection=collection)
                    split_docs = splitter.split_documents(docs)
                
                print(f"Split {file_name} into {len(split_docs)} chunks")

                with st.status(f"Uploading {file_name} chunks..."):
                    metadatas = [file_manifest for _ in split_docs]
                    file_chunks = [doc.page_content for doc in split_docs]
                    add_chroma_file_chunks(analytiq_config=analytiq_config,
                                           collection_name=collection_name,
                                           metadatas=metadatas,
                                           file_chunks=file_chunks)

                    print(f"Uploaded {file_name} chunks to {collection_name}")
                    # Update the state
                    st.session_state.file_in_collection[collection_name] = True
            
            if st.session_state.file_in_collection[collection_name] and not checkbox:
                # Will remove this file from this collection
                delete_chroma_file_chunks(analytiq_config=analytiq_config,
                                          collection_name=collection_name,
                                          file_manifest=file_manifest)

                st.info(f"Deleted {file_name} chunks from {collection_name}")

                # Update the state
                st.session_state.file_in_collection[collection_name] = False

    print(f"st.session_state   end: {st.session_state}")


display_upload_files()

# Set up the page footer
utils.page_footer()