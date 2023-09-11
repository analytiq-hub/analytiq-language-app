import os
import chromadb
import uuid
from chromadb.config import Settings
from langchain.vectorstores import Chroma
from langchain.embeddings.sentence_transformer import SentenceTransformerEmbeddings
from chromadb.utils import embedding_functions


import streamlit as st

def get_chroma_client(analytiq_config: dict = {},
                      analytiq_collections: dict = {}):
    """
    Get a ChromaDB client.

    Args:
        analytiq_config (dict, optional): The ChromaDB configuration. Defaults to {}.
        analytiq_collections (dict, optional): The ChromaDB collections. Defaults to {}.

    Returns:
        ChromaDB client.
    """
    if "chroma_client" not in st.session_state:
        # Create the client
        chroma_client = chromadb.HttpClient(host=analytiq_config["chroma_host"],
                                            port=analytiq_config["chroma_port"], 
                                            settings=Settings(allow_reset=True))
        st.session_state.chroma_client = chroma_client

    chroma_client = st.session_state.chroma_client
 
    # Get the list of collections
    if "chroma_collections" not in st.session_state:
        st.session_state.chroma_collections = {}
    
    for collection_name in analytiq_collections:
        # Ensure that the collection handle has been created
        if collection_name not in st.session_state.chroma_collections:
            embedding_functions = analytiq_collections[collection_name]["embedding"]
            chroma_collection = chroma_client.get_or_create_collection(name=collection_name,
                                                                       embedding_function=embedding_functions)
            st.session_state.chroma_collections[collection_name] = chroma_collection

    return chroma_client

def get_chroma_collection(analytiq_config: dict = {},
                          analytiq_collections: dict = {},
                          collection_name: str = "default"):
    """
    Get a Chroma collection.

    Args:
        analytiq_config (dict, optional): The ChromaDB configuration. Defaults to {}.
        collection_name (str, optional): The name of the collection. Defaults to "public_records".
        embedding_function (str, optional): The name of the embedding function. Defaults to "all-MiniLM-L6-v2".

    Returns:
        ChromaDB collection.
    """
    if "chroma_collection" not in st.session_state:
        # Initialize the collections
        st.session_state.chroma_collections = {}
    
    # Do we have the collection already?
    if collection_name in st.session_state.chroma_collections:
        return st.session_state.chroma_collections[collection_name]

    # We will create the collection

    # Create the client
    chroma_client = get_chroma_client(analytiq_config=analytiq_config)

    # Does the collection exist?
    try:
        chroma_collection = chroma_client.get_collection(name=collection_name)
    except:
        # Create the embedding function
        embedding_function = embedding_functions.SentenceTransformerEmbeddingFunction(model_name="all-MiniLM-L6-v2")

        # Create the collection
        chroma_collection = chroma_client.create_collection(name=collection_name,
                                                            embedding_function=embedding_function)
        
        st.success(f"Created chroma collection {collection_name}")

    # Save the collection and return
    st.session_state.chroma_collections[collection_name] = chroma_collection
    return st.session_state.chroma_collections[collection_name]

def delete_chroma_collection(analytiq_config: dict, 
                             analytiq_collections: dict,
                             collection_name: str):
    """
    Delete the Chroma collection.
    """

    if collection_name not in analytiq_collections:
        st.info(f"Chroma collection {collection_name} does not exist.")
        return True
    
    # Get the client before checking the collection name
    chroma_client = get_chroma_client(analytiq_config=analytiq_config, 
                                      analytiq_collections=analytiq_collections)
    
    # Are there any files in the collection?
    chroma_collection = st.session_state.chroma_collections[collection_name]
    result = chroma_collection.get(limit=1, include=["metadatas"])
    if len(result['ids']) > 0:
        st.error(f"Cannot delete collection {collection_name} because it is not empty.")
        return False
    chroma_client.delete_collection(name=collection_name)
    del st.session_state.chroma_collections[collection_name]

    st.success(f"Deleted chroma collection {collection_name}")
    return True

def check_chroma_file(analytiq_config: dict, collection_name: str, file_manifest: dict) -> bool:
    """
    Return True if file is in the collection
    """
    # Get the collection
    chroma_collection = get_chroma_collection(analytiq_config=analytiq_config,
                                              collection_name=collection_name)

    # Check if the file is in the collection
    # Query the metadata only
    result = chroma_collection.get(limit=1, where={"uuid": file_manifest["uuid"]}, include=["metadatas"])
    if len(result['ids']) > 0:
        return True
    else:
        return False

def list_chroma_collection(analytiq_config: dict, collection_name: str):
    """
    List the Chroma collection.
    """

    # Get the collection
    chroma_collection = get_chroma_collection(analytiq_config=analytiq_config,
                                              collection_name=collection_name)

    fname_set = set()

    # Get the documents
    offset = 0
    while True:
        result = chroma_collection.get(limit=1000, offset=offset, include=["metadatas"])
        result_size = len(result["metadatas"])
        if result_size == 0:
            break
        offset += result_size
        for metadata in result["metadatas"]:
            fname_set.add(metadata["file_name"])
    
    return fname_set

def clear_chroma_collection(analytiq_config: dict, collection_name: str):
    """
    Clear the Chroma collection.
    """
    # Get the collection
    chroma_collection = get_chroma_collection(analytiq_config=analytiq_config,
                                              collection_name=collection_name)
    
    while True:
        result = chroma_collection.get(limit=1000, include=["metadatas"])
        if len(result['ids']) == 0:
            break
        chroma_collection.delete(result['ids'])
        st.info(f"Deleted {len(result['ids'])} chunks from {collection_name}")

def add_chroma_file_chunks(analytiq_config: dict, collection_name: str, 
                           metadatas: dict, file_chunks: list):
    """
    Upload a file to the Chroma collection.

    Args:
        analytiq_config (dict): The Analytiq configuration.
        collection_name (str): The name of the collection.
        metadatas (dict): The list of file manifests.
        file_chunks (list): The file chunks.
    """
    # Get the collection
    chroma_collection = get_chroma_collection(analytiq_config=analytiq_config,
                                              collection_name=collection_name)
    
    # How many chunks?
    n_chunks = len(file_chunks)

    # Create the ids and metadatas
    ids = [str(uuid.uuid1()) for _ in range(n_chunks)]

    # Upload the file to the collection
    chroma_collection.add(ids=ids, metadatas=metadatas, documents=file_chunks)

def delete_chroma_file_chunks(analytiq_config: dict, collection_name: str, file_manifest: dict):
    """
    Delete a file from the Chroma collection.
    """
    # Get the collection
    chroma_collection = get_chroma_collection(analytiq_config=analytiq_config,
                                              collection_name=collection_name)

    # Delete the file from the collection
    chroma_collection.delete(where={"uuid": file_manifest["uuid"]})

@st.cache_resource(ttl="1h")
def get_chroma_retriever(analytiq_config: dict = {},
                         collection_name: str = "default",
                         search_k: int = 2,
                         fetch_k: int = 4) -> Chroma:
    """
    Get a Chroma collection retriever from the ChromaDB server.

    Args:
        collection_name (str, optional): The name of the collection. Defaults to "public_records".
        search_k (int, optional): The number of documents to search. Defaults to 2.
        fetch_k (int, optional): The number of documents to fetch. Defaults to 4.

    Returns:
        Chroma: A Chroma collection.
    """
    client = get_chroma_client(analytiq_config=analytiq_config)
    embedding_function = SentenceTransformerEmbeddings(model_name="all-MiniLM-L6-v2")
    chroma_collection = Chroma(client=client, 
                               collection_name=collection_name, 
                               embedding_function=embedding_function)

    return chroma_collection.as_retriever(search_type="mmr", 
                                          search_kwargs={"k": search_k, 
                                                         "fetch_k": fetch_k})
