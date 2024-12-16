#!/bin/bash

set -e

groupadd -g ${CONTAINER_GID} -o ${CONTAINER_UNAME}
useradd --no-log-init -m -u ${CONTAINER_UID} -g ${CONTAINER_GID} -o -s /bin/bash ${CONTAINER_UNAME}

echo "export PYTHONPATH=${CONTAINER_WORKDIR}" >> /home/${CONTAINER_UNAME}/.bashrc
cd /home/${CONTAINER_UNAME}

if (( $# < 1 ))
then
    su - ${CONTAINER_UNAME}
else
    su ${CONTAINER_UNAME} -c "$@"
fi
