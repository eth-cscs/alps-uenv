#!/bin/bash

#SBATCH --job-name=stackinator-paraview
#SBATCH --time=04:00:00
#SBATCH --nodes=1
#SBATCH --partition=nvgpu
#SBATCH --account=csstaff
#SBATCH --output=/users/biddisco/stackinator-output.txt
#SBATCH --error=/users/biddisco/stackinator-error.txt

export LC_ALL=en_US.UTF-8
unalias cp

echo "Setup build dir"
BUILD_DIR=/dev/shm/biddisco
# rm -rf ${BUILD_DIR}/*
mkdir -p ${BUILD_DIR}
mkdir -p ${BUILD_DIR}/tmp

echo "Execute stackinator"
cd $HOME/stackinator
./bin/stack-config -b ${BUILD_DIR} -r $HOME/alps-spack-stacks/hohgant-paraview --debug

echo "Trigger build"
cd ${BUILD_DIR}

# copy the spack build-cache gpg key to place where bubblewrap will map /tmp folder 
cp $HOME/.ssh/gpg-spack-paraview* ${BUILD_DIR}/tmp/

# build the squashfs image - bubblewrap is used inside the makefile
env --ignore-environment LC_ALL=en_US.UTF-8 PATH=/usr/bin:/bin:${BUILD_DIR}/spack/bin make store.squashfs -j32

echo "Copy generated squashfs file"
DATE=$(date +%F)
cp /dev/shm/biddisco/store.squashfs /scratch/e1000/biddisco/hohgant-paraview-$DATE.squashfs

# -----------------------------------------
# debug : create a shell using the spack setup used to create the squashfs
# -----------------------------------------
# $BUILD_DIR/bwrap-mutable-root.sh --tmpfs ~ --bind $BUILD_DIR/tmp /tmp --bind $BUILD_DIR/store /user-environment env --ignore-environment PATH=/usr/bin:/bin:${BUILD_DIR}/spack/bin SPACK_SYSTEM_CONFIG_PATH=/user-environment/config SPACK_USER_CACHE_PATH=$BUILD_DIR/cache /bin/bash --norc --noprofile

