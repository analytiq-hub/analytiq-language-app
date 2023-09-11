#!/usr/bin/env python3

import os
from pathlib import Path

from unstructured.partition.pdf import partition_pdf
import weaviate

from abstract_extractor import AbstractExtractor


WEAVIATE_PORT=8081

# Connect to Weaviate
client = weaviate.Client(
    url=f"http://localhost:{WEAVIATE_PORT}",  # Replace with your endpoint
)

batch_size = 20
class_name = "Document"
class_properties = ["filename"]
cursor = None


def get_batch_with_cursor(client, class_name, class_properties, batch_size, cursor=None):

    query = (
        client.query.get(class_name, class_properties)
        # Optionally retrieve the vector embedding by adding `vector` to the _additional fields
        .with_additional(["id vector"])
        .with_limit(batch_size)
    )

    if cursor is not None:
        return query.with_after(cursor).do()
    else:
        return query.do()
    
# Batch import all objects to the target instance
while True:
    # From the SOURCE instance, get the next group of objects
    results = get_batch_with_cursor(client, class_name, class_properties, batch_size, cursor)

    # If empty, we're finished
    if len(results["data"]["Get"][class_name]) == 0:
        break

    # Otherwise, add the objects to the batch to be added to the target instance
    objects_list = results["data"]["Get"][class_name]

    for retrieved_object in objects_list:
        print(retrieved_object.keys())

    # Update the cursor to the id of the last retrieved object
    cursor = results["data"]["Get"][class_name][-1]["_additional"]["id"]
