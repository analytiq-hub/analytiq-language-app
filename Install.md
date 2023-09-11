# Install for Analytiq App

* The Analytiq app installs on Linux.
* Ubuntu, Fedora distributions have been tested

Steps
* [Install Docker](https://docs.docker.com/engine/install/ubuntu/)
* A GPU is not required to run most Analytiq App functions
    * If a GPU is available, install the following:
        * CUDA drivers
        * NVIDIA container runtime
        * Check that `nvidia-smi` works both inside and outside the container
        * Follow steps [here](https://bitdribble.github.io/2023/08/24/ubuntu-nvidia/), for example
* Set up the python virtual environment
    * Install pip (steps are distribution-specific)
    * `pip install --upgrade pip` to upgrade to latest version
    * `pip install python-venv` to install the virtual environment
    * `mkdir ~/.venv; python -m venv ~/.venv/analytiq` will create the virtual env
    * `. ~/.venv/analytiq/bin/activate` will start the virtual env shell
* At this point, you are almost ready to run `pip install -r requirements.txt`. But a few more things need to be done in preparation:
    * Install development tools: 
    * Install MySql:
        * On Fedora
            * `sudo dnf install mariadb-server mariadb-devel`
            * `sudo systemctl enable mariadb-server`
            * `sudo systemctl start mariadb-server`
        * On Ubuntu - follow different steps
    * Install software dependencies
        * On Fedora:
          * `sudo dnf groupinstall "Development Tools" "Development Libraries"`
          * `sudo dnf install gcc-c++`
          * `sudo dnf install python3-devel`
        * On Ubuntu
          * Follow similar steps
    * Install torch:
        * `pip install torch`
* Now you can run `pip install -r requirements.txt`