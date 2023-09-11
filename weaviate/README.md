Steps:
- Install docker & docker-compose
- Use the `docker-compose.yaml` from this folder
- Note that the 8080 port is already in use by Airbyte. We changed the Weaviate port to 8081.
- `sudo mkdir /var/weaviate; sudo chmod 777 /var/weaviate`
- `docker-compose up -d` from this folder to start
- `docker-compose down` when shutting down