#!/bin/bash

# using pip and virtualenv
sudo apt-get -y install python-pip python-virtualenv python-dev libxml2-dev libxslt-dev libssl-dev libffi-dev libpq-dev python-lxml libxslt1-dev

virtualenv --python=python2.7 env
env/bin/pip install --upgrade pip
env/bin/pip install -r requirements.txt

