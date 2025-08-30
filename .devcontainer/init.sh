#!/bin/bash

server_port=8000

# install requirements dev

pip install --upgrade pip

pip install pip-review pip-tools

pip-compile -U --output-file requirements-dev.txt requirements-dev.in

pip install -r requirements-dev.txt

pip-sync requirements-dev.txt

pip-review --local

