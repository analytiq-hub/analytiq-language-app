#!/usr/bin/env python3

import os
from pathlib import Path

from abstract_extractor import AbstractExtractor

import json

import tqdm
from unstructured.partition.pdf import partition_pdf
from unstructured.staging.weaviate import create_unstructured_weaviate_class, stage_for_weaviate
import weaviate
from weaviate.util import generate_uuid5

# Based on https://github.com/Unstructured-IO/unstructured/blob/main/examples/weaviate/weaviate.ipynb
# and https://weaviate.io/blog/ingesting-pdfs-into-weaviate

WEAVIATE_PORT=8081

# Connect to Weaviate
client = weaviate.Client(
    url=f"http://localhost:{WEAVIATE_PORT}",  # Replace with your endpoint
)

unstructured_class_name = "Document"
unstructured_class = create_unstructured_weaviate_class(unstructured_class_name)
#unstructured_class["vectorizer"] = "text2vec-openai"
unstructured_class["moduleConfig"] = {
        "generative-openai": {},
#        "text2vec-openai": {"model": "ada", "modelVersion": "002", "type": "text"},
    }

client.schema.delete_all()
client.schema.create_class(unstructured_class)

# Get the folder 2 levels up
top = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

data_folder = f"{top}/data"

data_objects = []

for path in Path(data_folder).iterdir():
    if path.suffix != ".pdf":
        continue

    print(f"Processing {path.name}...")

    # "fast" strategy ends up skipping most of the text. Certainly skips the tables.
    # Need `pip install git+https://github.com/facebookresearch/detectron2.git` installed 
    # in order to get `unstructured` to parse pdfs with `hi_res` strategy
    elements = partition_pdf(filename=path, strategy="hi_res")

    data_objects = stage_for_weaviate(elements)

    with client.batch(batch_size=10) as batch:
        for data_object in tqdm.tqdm(data_objects):
            batch.add_data_object(
                data_object,
                unstructured_class_name,
                uuid=generate_uuid5(data_object),
            )