#!/bin/bash

#SBATCH --job-name=stackinator-paraview
#SBATCH --time=04:00:00
#SBATCH --nodes=1
#SBATCH --partition=nvgpu
#SBATCH --account=csstaff
#SBATCH --output=/users/biddisco/stackinator-output.txt
#SBATCH --error=/users/biddisco/stackinator-error.txt

export PYTHONUNBUFFERED=1

CLUSTER=oryx
STACKI_DIR=$SRC/alps-vcluster/stackinator
RECIPE_DIR=$SRC/alps-vcluster/alps-spack-stacks/recipes/paraview/turing
SYSTEM_DIR=$SRC/alps-vcluster/alps-cluster-config/$CLUSTER
BUILD_DIR=/dev/shm/biddisco

echo "Setup/clean build dir"
#rm -rf   ${BUILD_DIR}/*
mkdir -p ${BUILD_DIR}
mkdir -p ${BUILD_DIR}/tmp

echo "Execute stackinator"
$STACKI_DIR/bin/stack-config -s $SYSTEM_DIR -b ${BUILD_DIR} -r $RECIPE_DIR -c $RECIPE_DIR/cache-config.yaml --debug --develop

# build the squashfs image - bubblewrap is used inside the makefile
echo "Trigger build"
cd /dev/shm/biddisco
env --ignore-environment PATH=/usr/bin:/bin:`pwd`/spack/bin make store.squashfs -j32

echo "Copy generated squashfs file"
DATE=$(date +%F)
cp /dev/shm/biddisco/store.squashfs $SCRATCH/$CLUSTER-paraview-$DATE.squashfs

# -----------------------------------------
# debug : create a shell using the spack setup used to create the squashfs
# -----------------------------------------
# $BUILD_DIR/bwrap-mutable-root.sh --tmpfs ~ --bind $BUILD_DIR/tmp /tmp --bind $BUILD_DIR/store /user-environment env --ignore-environment PATH=/usr/bin:/bin:`pwd`/spack/bin SPACK_SYSTEM_CONFIG_PATH=/user-environment/config /bin/bash --norc --noprofile

