#/bin/bash

# change the following variables to set up code, input and output dirs
export HOST_WORK_DIR="/home/local/PARTNERS/dw640/ct_foundation_brain/"
export HOST_DATA_DIR="/home/local/PARTNERS/dw640/mnt/CAMCA/home/dufan.wu/research_output/ct_foundation_brain/"
export HOST_TMP_DIR="/home/local/PARTNERS/dw640/ct_foundation_brain_data/"

# The folder for the original data
export HOST_SRC_DATA_DIR="/home/local/PARTNERS/dw640/mnt/CAMCA/public_dataset/"

# get host user id to populate to the container
export HOST_USER_ID="$(id -u)"
export HOST_GROUP_ID="$(id -g)"
export HOST_USER_NAME=${USER}
export CONTAINER_WORKDIR="/workspace/ct_foundation_brain/"