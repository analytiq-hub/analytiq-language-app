# LLM App by Analytiq

## Install instructions

Clone the sandbox:
* `mkdir ~/build; cd ~/build`
* `git clone git@github.com:analytiq-hub/analytiq-language-app.git`
* Copy `.env_template` to `.env`, and set environment variables

Set up the virtual environment:
* On Ubuntu:
  * `sudo apt-get install python3.10-venv`
  * Install all `deb` packages from `docker/Dockerfile`
* On CentOS, RedHat, Fedora:
  * `sudo dnf install python3-virtualenv``
  * Install all `rpm` packages corresponding to `deb` packages from `docker/Dockerfile`
* `mkdir ~/.venv`
* `python -m venv ~/.venv/analytiq`
* `. ~/.venv/analytiq/bin/activate`

Install module dependencies inside the venv:
* `cd ~/build/analytiq-language-app`
* `pip install torch`
* `pip install -r requirements.txt`
* Note: You will need to install some Linux system packages manually, for example - the python development libraries, the mysql development libraries, and possibly others. Instructions differ depending on the Linux distribution.

Set up the Analytiq docstore:
* For now, get `analytiq-docstore.tgz` from Andrei, and untar it under `~/build`. You will end up with `~/build/analytiq-docstore`, which holds the public records database.
  * TO DO: I need to create from-scratch instructions on how to create `~/build/analytiq-docstore`

* Create & start the ChromaDB
  * Prerequisite: Install `docker`. TO DO: add instructions.
  * `cd ~/build`
  * `git clone git@github.com:chroma-core/chroma.git`
  * `cd chroma`
  * In `docker-compose.yaml`
    * Change port 8000 to 8002, to avoid conflict with Airbyte port 8000
    * Add `ALLOW_RESET=TRUE`

Here is the `docker-compose.yaml`:
```yaml
version: '3.9'

networks:
  net:
    driver: bridge

services:
  server:
    image: server
    build:
      context: .
      dockerfile: Dockerfile
    volumes:
      - ./:/chroma
      - index_data:/index_data
    command: uvicorn chromadb.app:app --reload --workers 1 --host 0.0.0.0 --port 8002 --log-config log_config.yml
    environment:
      - IS_PERSISTENT=TRUE
      - ALLOW_RESET=TRUE
      - CHROMA_SERVER_AUTH_PROVIDER=${CHROMA_SERVER_AUTH_PROVIDER}
      - CHROMA_SERVER_AUTH_CREDENTIALS_FILE=${CHROMA_SERVER_AUTH_CREDENTIALS_FILE}
      - CHROMA_SERVER_AUTH_CREDENTIALS=${CHROMA_SERVER_AUTH_CREDENTIALS}
      - CHROMA_SERVER_AUTH_CREDENTIALS_PROVIDER=${CHROMA_SERVER_AUTH_CREDENTIALS_PROVIDER}
    ports:
      - 8002:8002
    networks:
      - net

volumes:
  index_data:
    driver: local
  backups:
    driver: local
```
* Start ChromaDB
  * Do `docker-compose up -d --build` to bring up, and `docker-compose down` to bring down.

You are now ready to run the analytiq app:
* To run: `streamlit run Analytiq.py --server.port 8080`