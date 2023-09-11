#!/usr/bin/env python3

import os
from pathlib import Path

import weaviate
import json



WEAVIATE_PORT=8081

# Connect to Weaviate
client = weaviate.Client(
    url=f"http://localhost:{WEAVIATE_PORT}",  # Replace with your endpoint
)

response = (
    client.query
    .get("Document", ["text", "_additional {score}"])
    .with_bm25(
      query="schools"
    )
    .with_limit(2)
    .do()
)

print(json.dumps(response, indent=4))