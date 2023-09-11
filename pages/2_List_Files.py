import os
import streamlit as st


import utils
from config_utils import (
    get_analytiq_config,
    get_categories,
    get_collections,
    get_docs,
    save_docs,
)
from chroma_utils import (
    check_chroma_file
) 

# Initialize the page
utils.page_init()

# This should be first streamlit command called
st.set_page_config(page_title="List Files", layout="wide")
st.title("List Files")

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

edit_files = st.sidebar.checkbox("Edit Files", value=False, key="edit_files")

def display_files():
    """
    Display the files tab
    """
    
    st.text("")

    if edit_files:
        file_col, type_col, year_col, delete_col = st.columns([3, 3, 1, 1])
    else:  
        file_col, type_col, year_col, collection_col = st.columns([3, 3, 1, 1])
    with file_col:
        st.text("File")
    with type_col:
        st.text("Type")
    with year_col:
        st.text("Year")
    if edit_files:
        with delete_col:
            st.text("Delete")
    else:
        with collection_col:
            st.text("Collection")

    for file_manifest in analytiq_docs:
        if len(document_year) > 0 and file_manifest["year"] not in document_year:
            continue
        if len(document_type) > 0 and file_manifest["type"] not in document_type:
            continue

        if edit_files:
            file_col, type_col, year_col, delete_col = st.columns([3, 3, 1, 1])
        else:
            file_col, type_col, year_col, collection_col = st.columns([3, 3, 1, 1])

        # Display two dropdown menus for each file
        with file_col:
            # Create a download link to the file on disk
            file_name = file_manifest["file_name"]
            uuid = file_manifest["uuid"]
            full_file_name = f"{analytiq_config['docstore']}/doc/{uuid}/{file_name}"
            with open(full_file_name, "rb") as file:
                st.download_button(label=file_name, 
                                file_name=file_name,
                                mime="application/pdf",
                                data=file)

        with type_col:
            if edit_files:                
                # Get the index of the file_manifest["type"] in the list of types
                type_index = [i for i, type in enumerate(analytiq_categories["type"]) if type == file_manifest["type"]][0]
                file_manifest["type"] = st.selectbox(
                    "Type:",
                    analytiq_categories["type"], 
                    index = type_index,
                    key=f"type_{file_manifest['file_name']}",
                    label_visibility="collapsed"
                    )
            else:
                st.write(file_manifest["type"])
        with year_col:
            if edit_files:
                # Get the index of the file_manifest["year"] in the list of years
                year_index = [i for i, year in enumerate(["2023", "2022", "2021", "2020", "2019", "2018", "2017", "2016", "2015"]) if year == file_manifest["year"]][0]
                # Create a dropdown menu for the year
                file_manifest["year"] = st.selectbox("Year:", 
                                                ["2023", "2022", "2021", "2020", "2019", "2018", "2017", "2016", "2015"],
                                                index=year_index,
                                                key=f"year_{file_manifest['file_name']}",
                                                label_visibility="collapsed")
            else:
                st.write(file_manifest["year"])
        
        if edit_files:
            with delete_col:
                if st.button("Delete", key=f"delete_{file_manifest['file_name']}"):
                    # Delete the file
                    file_name = file_manifest["file_name"]
                    uuid = file_manifest["uuid"]
                    full_file_name = f"{analytiq_config['docstore']}/doc/{uuid}/{file_name}"
                    os.remove(full_file_name)
                    st.info(f"Deleted {full_file_name}")

                    # Delete the file manifest
                    analytiq_docs.remove(file_manifest)

                    # Save the docs
                    save_docs(analytiq_config=analytiq_config, docs=analytiq_docs)
        else:
            with collection_col:
                names = []
                for collection_name in analytiq_collections:
                    if check_chroma_file(analytiq_config=analytiq_config, 
                                         collection_name=collection_name,
                                         file_manifest=file_manifest):
                        names.append(collection_name)
                st.write(", ".join(names))

display_files()

# Set up the page footer
utils.page_footer()