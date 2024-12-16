#/bin/bash

source $(dirname $0)/../docker_paths.sh

# port forwarding is no longer needed -- they can be set directly through VSCode

docker run -it --runtime=nvidia --rm --name brain_ct_ddpm \
    --shm-size=256m --ipc=host \
    -v "$HOST_WORK_DIR":"$CONTAINER_WORKDIR" \
    -v "$HOST_DATA_DIR":"/mnt/data/" \
    -v "$HOST_TMP_DIR":"/mnt/tmp_data/" \
    -v "$HOST_SRC_TRAIN_DIR":"/mnt/src_train/" \
    -v "$HOST_SRC_TEST_DIR":"/mnt/src_test/" \
    -e CONTAINER_UID=${HOST_USER_ID} \
    -e CONTAINER_GID=${HOST_GROUP_ID} \
    -e CONTAINER_UNAME=${HOST_USER_NAME} \
    -e CONTAINER_WORKDIR=${CONTAINER_WORKDIR} \
    brain_ct_ddpm/main:1.0.0