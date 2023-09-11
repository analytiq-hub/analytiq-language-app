#!/usr/bin/env python3

import weaviate

WEAVIATE_PORT=8081

# Connect to Weaviate
client = weaviate.Client(
    url=f"http://localhost:{WEAVIATE_PORT}",  # Replace with your endpoint
)

class_obj = {
    "class": "Question",
    "vectorizer": "text2vec-openai",  # If set to "none" you must always provide vectors yourself. Could be any other "text2vec-*" also.
    "moduleConfig": {
        "text2vec-openai": {},
        "generative-openai": {}  # Ensure the `generative-openai` module is used for generative queries
    }
}

client.schema.delete_class("Question")
client.schema.create_class(class_obj)
