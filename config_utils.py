import os
import json
import copy
from datetime import datetime
import uuid
import streamlit as st

# Globals
categories_orig = {}
collections_orig = {}
docs_orig = {}

def init_analytiq_config(analytiq_config: dict = {}) -> None:
    """
    Initialize the ChromaDB configuration
    
    Args:
        analytiq_config (dict, optional): The ChromaDB configuration. Defaults to {}.
    """
    # Ensure the chroma folder structure is set up
    analytiq_docstore = analytiq_config["docstore"]
    os.makedirs(analytiq_docstore, exist_ok=True)
    os.makedirs(f"{analytiq_docstore}/doc", exist_ok=True)
    
    fname = f"{analytiq_docstore}/analytiq_docs.json"
    if not os.path.exists(fname):
        # By default, there are no documents
        json.dump({"schema_version": "1.0", "docs": []}, open(fname, "w"), indent=2)
        st.info(f"Created {fname}")
    
    fname = f"{analytiq_docstore}/analytiq_categories.json"
    if not os.path.exists(fname):
        # Default categories
        categories_def = {
            "type": [
                "Annual Town Reports",
                "Town Meeting Warrant", 
                "Brown Book",
                "School Budget",
                "Appropriation Committee Report",
                "Capital Expenditures Committee Report",
                "Community Preservation Committee Report",
                "Planning Board Report"
                ],
            "year": [
            ]
        }

        # Populate the past 10 years
        current_year = datetime.now().year
        categories_def["year"] = [str(year) for year in range(current_year, current_year-10, -1)]

        json.dump({"schema_version": "1.0", "categories": categories_def}, 
                  open(fname, "w"), indent=2)
        st.info(f"Created {fname}")

def get_analytiq_config() -> dict:
    """
    Get the ChromaDB configuration

    Returns:
        dict: A dictionary containing the ChromaDB configuration.
    """

    config = {
        "chroma_host": os.getenv("CHROMA_HOST"),
        "chroma_port": os.getenv("CHROMA_PORT"),
        "docstore": os.getenv("ANALYTIQ_DOCSTORE")
    }

    if config["chroma_host"] is None:
        st.error("CHROMA_HOST is not set in the .env file.")
        st.stop()
    if config["chroma_port"] is None:
        st.error("CHROMA_PORT is not set in the .env file.")
        st.stop()
    if config["docstore"] is None:
        st.error("ANALYTIQ_DOCSTORE is not set in the .env file.")
        st.stop()
    
    # Initialize the config
    init_analytiq_config(config)

    return config

def get_categories(analytiq_config: dict = {}) -> dict:
    """
    Get the categories configuration

    Args:
        analytiq_config (dict, optional): The ChromaDB configuration. Defaults to {}.
    
    Returns:
        dict: A dictionary containing the categories configuration.
    """
    global categories_orig

    analytiq_categories = json.load(open(f"{analytiq_config['docstore']}/analytiq_categories.json", "r"))
    categories = analytiq_categories["categories"]

    # Save the original categories
    categories_orig = copy.deepcopy(categories)

    return categories

def save_categories(analytiq_config: dict = {}, categories: dict = {}) -> None:
    """
    Save the categories configuration

    Args:
        analytiq_config (dict, optional): The ChromaDB configuration. Defaults to {}.
        categories (dict, optional): The categories configuration. Defaults to {}.
    """
    global categories_orig

    if categories == categories_orig:
        # Categories have not changed
        return

    analytiq_categories = {
        "schema_version": "1.0",
        "categories": categories
    }
    fname = f"{analytiq_config['docstore']}/analytiq_categories.json"
    json.dump(analytiq_categories, open(fname, "w"), indent=2)
    st.info(f"Saved {fname}")

    # Save the original categories
    categories_orig = copy.deepcopy(categories)

def get_collections(analytiq_config: dict = {}) -> dict:
    """
    Get the collections configuration

    Args:
        analytiq_config (dict, optional): The configuration. Defaults to {}.
    
    Returns:
        dict: A dictionary containing the collections configuration.
    """
    global collections_orig

    analytiq_collections = json.load(open(f"{analytiq_config['docstore']}/analytiq_collections.json", "r"))
    collections = analytiq_collections["collections"]

    # Save the original collections
    collections_orig = copy.deepcopy(collections)

    return collections

def save_collections(analytiq_config: dict = {}, collections: dict = {}) -> None:
    """
    Save the collections configuration

    Args:
        analytiq_config (dict, optional): The Analytiq configuration. Defaults to {}.
        collections (dict, optional): The collections configuration. Defaults to {}.
    """
    global collections_orig

    if collections == collections_orig:
        # Collections have not changed
        return

    analytiq_collections = {
        "schema_version": "1.0",
        "collections": collections
    }
    fname = f"{analytiq_config['docstore']}/analytiq_collections.json"
    json.dump(analytiq_collections, open(fname, "w"), indent=2)
    st.info(f"Saved {fname}")

    # Save the original collections
    collections_orig = copy.deepcopy(collections)

def get_docs(analytiq_config: dict = {}) -> dict:
    """
    Get the documents configuration

    Args:
        analytiq_config (dict, optional): The ChromaDB configuration. Defaults to {}.
    
    Returns:
        dict: A dictionary containing the documents configuration.
    """
    global docs_orig

    analytiq_docs = json.load(open(f"{analytiq_config['docstore']}/analytiq_docs.json", "r"))
    docs = analytiq_docs["docs"]

    # Save the original documents
    docs_orig = copy.deepcopy(docs)

    return docs

def save_docs(analytiq_config: dict = {}, docs: dict = {}) -> None:
    """
    Save the documents configuration

    Args:
        analytiq_config (dict, optional): The ChromaDB configuration. Defaults to {}.
        docs (dict, optional): The documents configuration. Defaults to {}.
    """
    global docs_orig

    if docs == docs_orig:
        # Documents have not changed
        return

    analytiq_docs = {
        "schema_version": "1.0",
        "docs": docs
    }
    fname = f"{analytiq_config['docstore']}/analytiq_docs.json"
    json.dump(analytiq_docs, open(fname, "w"), indent=2)
    st.info(f"Saved {fname}")

    # Save the original documents
    docs_orig = copy.deepcopy(docs)


@st.cache_data
def normalize_chroma_schema(analytiq_config: dict = {}) -> None:
    """
    Normalize the ChromaDB schema

    Args:
        analytiq_config (dict, optional): The ChromaDB configuration. Defaults to {}.
        categories (dict, optional): The ChromaDB categories. Defaults to {}.
        docs (dict, optional): The ChromaDB documents. Defaults to {}.
    """

    # Categories are already normalized

    # Normalize the docs
    docs = get_docs(analytiq_config)
    docs2 = []

    for doc in docs:
        if "uuid" not in doc:
            doc["uuid"] = str(uuid.uuid4())
            # Create the uuid folder
            os.makedirs(f"{analytiq_config['docstore']}/doc/{doc['uuid']}", exist_ok=True)
            # Move the file to the uuid folder
            fname1 = f"{analytiq_config['docstore']}/{doc['file_name']}"
            fname2 = f"{analytiq_config['docstore']}/doc/{doc['uuid']}/{doc['file_name']}"
            os.rename(fname1, fname2)
            st.info(f"Moved {fname1} to {fname2}")

        # Copy into the new docs list
        docs2.append({
            "file_name": doc["file_name"],
            "uuid": doc["uuid"],
            "type": doc["type"],
            "year": doc["year"]
        })

    # Save the docs
    save_docs(analytiq_config, docs2)