#!/bin/bash

#SBATCH --job-name=stackinator-paraview
#SBATCH --time=04:00:00
#SBATCH --nodes=1
#SBATCH --partition=normal
#SBATCH --account=csstaff
#SBATCH --output=/users/biddisco/stackinator-output.%j.txt
#SBATCH --error=/users/biddisco/stackinator-error.%j.txt
#SBATCH --constraint=mc

# -------------------------------------
function debug_output() {
    {
        echo ""
        echo "-------------------------------------"
        echo "-- $1"
        echo "-------------------------------------"
    }
}

# -------------------------------------
export PYTHONUNBUFFERED=1

# -------------------------------------
# useful variables
# -----------------------------------------"
debug_output "Setup env vars"
CLUSTER=eiger
IMAGE=paraview
ARCH=zen2
VARIANT=osmesa
VERSION=5.13.2
SPACK_ENV_NAME="${IMAGE}-${ARCH}-${VARIANT}-${VERSION}"
SRC=$HOME/src
STACKI_DIR=$SRC/alps-vcluster/stackinator
RECIPE_DIR=$SRC/alps-vcluster/alps-uenv/recipes/${IMAGE}/${VERSION}/${ARCH}
SYSTEM_DIR=$SRC/alps-vcluster/alps-cluster-config/${CLUSTER}
BUILD_DIR=/dev/shm/biddisco
DATE=$(date '+%Y-%m-%d')
SQUASHFS_IMAGE_NAME=$SCRATCH/${SPACK_ENV_NAME}-$DATE.squashfs

# -----------------------------------------"
http_proxy=http://proxy.cscs.ch:8080
https_proxy=$http_proxy

# -----------------------------------------"
debug_output "Setup/clean build dir"
rm   -rf ${BUILD_DIR}/*
mkdir -p ${BUILD_DIR}
mkdir -p ${BUILD_DIR}/tmp

# -----------------------------------------"
debug_output "Execute stackinator"
$STACKI_DIR/bin/stack-config -s $SYSTEM_DIR -b ${BUILD_DIR} -r $RECIPE_DIR -c $HOME/src/uenv-cache-config.yaml --debug --develop

# -----------------------------------------"
debug_output "cd $BUILD_DIR"
cd $BUILD_DIR

# -----------------------------------------"
debug_output "make squashfs image"
env --ignore-environment PATH=/usr/bin:/bin:`pwd`/spack/bin HOME="$HOME" http_proxy=$http_proxy https_proxy=$https_proxy no_proxy="$no_proxy" cluster=$CLUSTER make store.squashfs -j32

# -----------------------------------------"
debug_output "Force push anything that was built successfully"
env --ignore-environment PATH=/usr/bin:/bin:`pwd`/spack/bin make cache-force

# -----------------------------------------"
debug_output "check generated squashfs file"
unalias cp
if [ -f "$BUILD_DIR/store.squashfs" ]; then
    echo "Copy generated file to $SQUASHFS_IMAGE_NAME"
    cp -f $BUILD_DIR/store.squashfs $SQUASHFS_IMAGE_NAME
else
    echo "ERROR: $BUILD_DIR/store.squashfs does not exist"
fi

# -----------------------------------------
# debug : create a shell using the spack setup used to create the squashfs
# -----------------------------------------
# $BUILD_DIR/bwrap-mutable-root.sh --tmpfs ~ --bind $BUILD_DIR/tmp /tmp --bind $BUILD_DIR/store /user-environment env --ignore-environment PATH=/usr/bin:/bin:`pwd`/spack/bin https_proxy=$https_proxy http_proxy=$http_proxy no_proxy="$no_proxy" SPACK_SYSTEM_CONFIG_PATH=/user-environment/config /bin/bash --norc --noprofile

# -----------------------------------------"
debug_output "Cleanup /dev/shm directories"
rm -rf   ${BUILD_DIR}/*

# -----------------------------------------"
debug_output "HOWTO: mount the squashfs image for editing"
echo "unsquashfs -d $BUILD_DIR $SQUASHFS_IMAGE_NAME"
echo "bwrap --dev-bind / / --bind $BUILD_DIR /user-environment bash"
