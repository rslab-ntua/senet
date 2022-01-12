#!/usr/bin/env bash

# Based on Ubuntu version must be fixed to install GDAL>=3.0
sudo add-apt-repository ppa:ubuntugis/ppa && sudo apt-get update
sudo apt update
sudo apt install gdal-bin
sudo apt install libgdal-dev
export CPLUS_INCLUDE_PATH=/usr/include/gdal
export C_INCLUDE_PATH=/usr/include/gdal
# then pip install GDAL
