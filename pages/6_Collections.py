import streamlit as st
from tqdm import tqdm

from langchain.text_splitter import Language

import utils
from config_utils import (
    get_analytiq_config,
    get_categories,
    get_collections,
    get_docs,
    save_collections,
)
from collection_utils import (
    get_collection_loader,
    get_collection_splitter
)
from chroma_utils import (
    get_chroma_collection,
    delete_chroma_collection,
    check_chroma_file,
    list_chroma_collection,
    clear_chroma_collection,
    add_chroma_file_chunks
)

# Initialize the page
utils.page_init()

# This should be first streamlit command called
st.set_page_config(page_title="Collections", layout="wide")
st.title("Collections")

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

def display_collections():
    """
    Display the collections
    """

    col1, col2, col3 = st.columns(3)

    with col2:
        # Text input for new category
        value = st.text_input("Add a new collection:")

        # Button to add new category
        if st.button("Add collection"):
            if value and value not in analytiq_collections:
                analytiq_collections[value] = {
                    "parser": "unstructured",
                    "length_function": "characters",
                    "splitter": "CharacterTextSplitter",
                    "chunk_size": 1000,
                    "chunk_overlap": 100,
                    "embedding": "all-MiniLM-L6-v2"
                }
                get_chroma_collection(analytiq_config=analytiq_config,
                                      analytiq_collections=analytiq_collections,
                                      collection_name = value)
                st.success(f"Added collection: {value}")
    with col3:
        if len(analytiq_collections) > 1:
            values = list(analytiq_collections.keys())
            # Remove the default collection
            values.remove("default")

            selected_values_to_remove = st.multiselect("Select collections to remove:", 
                                                        values)
            removed_collections = []
            

            if st.button(f"Remove selected collections"):
                for value in selected_values_to_remove:
                    if value in analytiq_collections:
                        ret = delete_chroma_collection(analytiq_config=analytiq_config,
                                                       analytiq_collections=analytiq_collections,
                                                       collection_name = value)
                        if ret:
                            del analytiq_collections[value]
                            removed_collections.append(value)
                if len(removed_collections) > 0:
                    st.success(f"Removed collections: {', '.join(removed_collections)}")

        else:
            st.text("No collection to remove")

    with col1:
        st.text("Collections")
        st.write(list(analytiq_collections.keys()))

    for collection_name, collection in analytiq_collections.items():
        # Insert horizontal line
        st.markdown("---")

        col1, col2, col3 = st.columns(3)

        with col3:
            # Text input for new category
            key = f"parser-{collection_name}"
            options = ["unstructured", "pypdf"]
            index = 0
            if key in st.session_state:
                index = options.index(st.session_state[key])
            else:
                index = options.index(collection["parser"])
            parser = st.selectbox("Select Parser:", 
                                  options=options, 
                                  index=index,
                                  key=key,
                                  help="Choose a parser to use for the collection.")
            collection["parser"] = parser

            key = f"length-function-{collection_name}"
            options = ["characters", "tokens"]
            index = 0
            if key in st.session_state:
                index = options.index(st.session_state[key])
            else:
                index = options.index(collection["length_function"])
            length_function = st.selectbox("Length Function:", 
                                            options=options, 
                                            index=index,
                                            key=key,
                                            help="Choose a Length Function")
            collection["length_function"] = length_function

            key = f"splitter-{collection_name}"
            options = [
                "RecursiveCharacterTextSplitter", 
                "CharacterTextSplitter",
            ]
            options += [str(v) for v in Language]
            index = 0
            if key in st.session_state:
                index = options.index(st.session_state[key])
            else:
                index = options.index(collection["splitter"])
            splitter = st.selectbox("Splitter:", 
                                    options=options, 
                                    index=index,
                                    key=key,
                                    help="Choose a splitter")
            collection["splitter"] = splitter

            col3_1, col3_2 = st.columns(2)

            with col3_1:
                key = f"chunk-size-{collection_name}"
                if key in st.session_state:
                    value = st.session_state[key]
                else:
                    value = collection["chunk_size"]
                chunk_size = st.number_input(label="Chunk Size", 
                                            min_value=1, 
                                            max_value=10000,
                                            value=value,
                                            key=key,
                                            help="Number of characters to process at a time.")
                collection["chunk_size"] = chunk_size

            with col3_2:
                key = f"chunk-overlap-{collection_name}"
                if key in st.session_state:
                    value = st.session_state[key]
                else:
                    value = collection["chunk_overlap"]
                chunk_overlap = st.number_input("Chunk Overlap",
                                                min_value=0,
                                                max_value=1000,
                                                value=value, 
                                                key=key,
                                                help="Number of characters to process at a time.")
                collection["chunk_overlap"] = chunk_overlap

            key = f"embedding-{collection_name}"
            options = ["all-MiniLM-L6-v2", "text-embedding-ada-002"]
            index = 0
            if key in st.session_state:
                index = options.index(st.session_state[key])
            else:
                index = options.index(collection["embedding"])
            embedding = st.selectbox("Embedding:",
                                     options=options,
                                     index=index,
                                     key=key,
                                     help="Choose an embedding to use for the collection.")
            collection["embedding"] = embedding

        with col1:
            st.text(collection_name)
            st.write(collection)
        
        with col2:
            st.text("Edit Collection")
            upload_all_files_key=f"upload_all_files_{collection_name}"
            list_all_files_key  =f"list_all_files_{collection_name}"
            delete_all_files_key=f"delete_all_files_{collection_name}"

            upload_all_files = st.button("Upload all files", key=upload_all_files_key)
            list_all_files   = st.button("List all files",   key=list_all_files_key)
            delete_all_files = st.button("Delete all files", key=delete_all_files_key)

            if upload_all_files:
                # Get the splitter
                splitter = get_collection_splitter(analytiq_config=analytiq_config,
                                                   collection=collection)

                # Loop over the files
                for file_manifest in tqdm(analytiq_docs, desc=f"Uploading files to {collection_name}"):
                    # Check if the file is already in the collection
                    if check_chroma_file(analytiq_config=analytiq_config, 
                                         collection_name=collection_name, 
                                         file_manifest=file_manifest):
                        continue

                    # Get the file path
                    file_name = file_manifest["file_name"]
                    id = file_manifest["uuid"]
                    file_path = f"{analytiq_config['docstore']}/doc/{id}/{file_name}"

                    # Get the loader
                    loader = get_collection_loader(analytiq_config=analytiq_config,
                                                    collection=collection,
                                                    file_path=file_path)

                    # Get the text
                    with st.status(f"Parsing {file_name}..."):
                        docs = loader.load()

                    # Split the text into chunks
                    with st.status(f"Splitting {file_name}..."):
                        split_docs = splitter.split_documents(docs)

                    # Add the chunks to the collection
                    with st.status(f"Uploading {file_name} chunks..."):
                        metadatas = [file_manifest for _ in split_docs]
                        file_chunks = [doc.page_content for doc in split_docs]
                        add_chroma_file_chunks(analytiq_config=analytiq_config,
                                               collection_name=collection_name,
                                               metadatas=metadatas,
                                               file_chunks=file_chunks)

                st.success(f"Uploaded all files to {collection_name}")

            if list_all_files:
                fname_set = list_chroma_collection(analytiq_config=analytiq_config, 
                                                   collection_name=collection_name)
                
                if len(fname_set) > 0:
                    for fname in fname_set:
                        st.write(fname)
                else:
                    st.info("No files in collection")


            if delete_all_files:
                clear_chroma_collection(analytiq_config=analytiq_config, 
                                        collection_name=collection_name)
                st.success(f"Deleted all files from {collection_name}")


    # Save the collections if they have changed. This routine checks internally if the collections have changed.
    save_collections(analytiq_config=analytiq_config, collections=analytiq_collections)

display_collections()

# Set up the page footer
utils.page_footer()