#!/bin/bash

#SBATCH --job-name=stackinator-paraview
#SBATCH --time=04:00:00
#SBATCH --nodes=1
#SBATCH --partition=normal
#SBATCH --account=csstaff
#SBATCH --output=/users/biddisco/stackinator-output.%j.txt
#SBATCH --error=/users/biddisco/stackinator-error.%j.txt

export PYTHONUNBUFFERED=1

CLUSTER=todi
ARCH=gh200
IMAGE=paraview
VARIANT=
SRC=/users/biddisco/src
STACKI_DIR=$SRC/alps-vcluster/stackinator
RECIPE_DIR=$SRC/alps-vcluster/alps-uenv/recipes/${IMAGE}${VARIANT}/${ARCH}
SYSTEM_DIR=$SRC/alps-vcluster/alps-cluster-config/${CLUSTER}
BUILD_DIR=/dev/shm/biddisco
SPACK_ENV_NAME="paraview-gh200-egl-cuda-5.13"
DATE=$(date '+%Y-%m-%d')
SQUASHFS_IMAGE_NAME=$SCRATCH/${SPACK_ENV_NAME}-$DATE.squashfs

echo "# -----------------------------------------"
echo "Setup/clean build dir"
rm   -rf ${BUILD_DIR}/*
mkdir -p ${BUILD_DIR}
mkdir -p ${BUILD_DIR}/tmp

echo "# -----------------------------------------"
echo "Execute stackinator"
$STACKI_DIR/bin/stack-config -s $SYSTEM_DIR -b ${BUILD_DIR} -r $RECIPE_DIR -c $RECIPE_DIR/cache-config.yaml --debug --develop

# build the squashfs image - bubblewrap is used inside the makefile
echo "# -----------------------------------------"
echo "Trigger build"
cd /dev/shm/biddisco
export http_proxy=http://proxy.cscs.ch:8080
export https_proxy=$http_proxy
env --ignore-environment PATH=/usr/bin:/bin:`pwd`/spack/bin HOME="$HOME" http_proxy=$http_proxy https_proxy=$https_proxy no_proxy="$no_proxy" make store.squashfs -j32

echo "# -----------------------------------------"
echo "Force push anything that was built successfully"
env --ignore-environment PATH=/usr/bin:/bin:`pwd`/spack/bin make cache-force

echo "# -----------------------------------------"
unalias cp
if [ -f "/dev/shm/biddisco/store.squashfs" ]; then
    echo "Copy generated file to $SQUASHFS_IMAGE_NAME"
    cp -f /dev/shm/biddisco/store.squashfs $SQUASHFS_IMAGE_NAME
else
    echo "ERROR: /dev/shm/biddisco/store.squashfs does not exist"
fi

# -----------------------------------------
# debug : create a shell using the spack setup used to create the squashfs
# -----------------------------------------
# $BUILD_DIR/bwrap-mutable-root.sh --tmpfs ~ --bind $BUILD_DIR/tmp /tmp --bind $BUILD_DIR/store /user-environment env --ignore-environment PATH=/usr/bin:/bin:`pwd`/spack/bin https_proxy=$https_proxy http_proxy=$http_proxy no_proxy="$no_proxy" SPACK_SYSTEM_CONFIG_PATH=/user-environment/config /bin/bash --norc --noprofile

echo "# -----------------------------------------"
echo "# REMOVE THE CLEANUP WHEN DEBUGGING"
echo "# -----------------------------------------"
echo "Clean up the /dev/shm directories"
#rm -rf   ${BUILD_DIR}/*

echo "# -----------------------------------------"
echo "# DEBUGGING"
echo "unsquashfs -d /dev/shm/biddisco $SQUASHFS_IMAGE_NAME"
echo "bwrap --dev-bind / / --bind /dev/shm/biddisco /user-environment bash"
