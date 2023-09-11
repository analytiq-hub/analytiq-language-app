import tiktoken

from langchain.document_loaders import UnstructuredPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter, CharacterTextSplitter, Language
from langchain.document_loaders.pdf import PyPDFLoader


def get_collection_loader(analytiq_config: dict, 
                          collection: dict,
                          file_path: str) -> object:
    """
    Get the loader for the collection

    Args:
        analytiq_config (dict): The configuration.
        collection (dict): The collection configuration.
        file_path (str): The file path.

    Returns:
        object: The loader object.
    """
    if collection["parser"] == "unstructured":
        loader = UnstructuredPDFLoader(file_path, show_progress=True, use_multithreading=True)
    elif collection["parser"] == "pypdf":
        loader = PyPDFLoader(file_path)
    else:
        raise ValueError(f"Unknown parser: {collection['parser']}")

    return loader

_enc = tiktoken.get_encoding("cl100k_base")
def cl100k_base_length_function(text: str) -> int:
    return len(_enc.encode(text))


def get_collection_splitter(analytiq_config: dict,
                            collection: dict):
    """
    Get the colection splitter
    
    Args:
        analytiq_config (dict): The configuration.
        collection (dict): The collection configuration.
    """
    length_function_choice = collection["length_function"]
    splitter_choice = collection["splitter"]
    chunk_size = collection["chunk_size"]
    chunk_overlap = collection["chunk_overlap"]

    if length_function_choice == "characters":
        length_function = len
    elif length_function_choice == "tokens":
        length_function = cl100k_base_length_function
    else:
        raise ValueError(f"Unknown length function: {length_function_choice}")

    if splitter_choice == "CharacterTextSplitter":
        splitter = CharacterTextSplitter(separator="\n\n",
                                         chunk_size=chunk_size, 
                                         chunk_overlap=chunk_overlap,
                                         length_function=length_function)
    elif splitter_choice == "RecursiveCharacterTextSplitter":
        splitter = RecursiveCharacterTextSplitter(chunk_size=chunk_size, 
                                                  chunk_overlap=chunk_overlap,
                                                  length_function=length_function)
    elif "Language." in splitter_choice:
        language = splitter_choice.split(".")[1].lower()
        splitter = RecursiveCharacterTextSplitter.from_language(language,
                                                                chunk_size=chunk_size,
                                                                chunk_overlap=chunk_overlap,
                                                                length_function=length_function)
    else:
        raise ValueError(f"Unknown splitter: {splitter_choice}")
    
    if splitter == None:
        raise ValueError(f"Unable to get a splitter for {splitter_choice}")

    return splitter