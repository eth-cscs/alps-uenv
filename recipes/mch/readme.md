The software stacks for MCH, for use on Balfrin and Tasna.

## Versioning

The MCH software stack is released as versions: v1, v2, v3, etc, which are mounted at `/user-environment/v[123...]`, not the default `/user-environment` mount point.
These mount points are created specifically on the MCH systems.

Each version is tagged `mch-<system>-v<N>` where `<system>` is one of `balfrin` or `tasna`, and `N` is the software stack version number.

Notes about the versions are available on the CSCS internal confluence:

https://confluence.cscs.ch/display/MCH/Balfrin+PE

## Building

Because the MCH stack is not installed in the default location, we set some environment variables, which are used to manually configure the installation location when calling stack-config.

```bash
#!/bin/bash

export TAG=balfrin-v5
# set the mount point - development/testing versions are installed directly on
# $SCRATCH. The deployment version at /mch-environment/vX the build has to be
# rerun with MOUNT set appropriately
#export MOUNT=$SCRATCH/mch-environment/v6-rc2
export MOUNT=/mch-environment/v5
export CACHE_PATH=$SCRATCH/uenv-cache/

mkdir work
cd work
work=$(pwd)

echo
echo === getting stackinator
echo
git clone --quiet git@github.com:eth-cscs/stackinator.git
(cd stackinator; ./bootstrap.sh)
export PATH=$work/stackinator/bin:$PATH

echo
echo === getting recipe
echo
git clone --quiet git@github.com:eth-cscs/alps-spack-stacks.git
(cd alps-spack-stacks && git checkout $TAG)
recipes=$work/alps-spack-stacks/recipes

echo
echo === getting cluster configuration
echo
git clone --quiet git@github.com:eth-cscs/alps-cluster-config.git
systems=$work/alps-cluster-config

# Note, you will need to have created a key:
# https://eth-cscs.github.io/stackinator/build-caches/
echo "root: $CACHE_PATH" > cache.yaml
echo "key: $CACHE_PATH/push-key.gpg" >> cache.yaml

echo
echo === configuring the build stack
echo
stack-config -b /dev/shm/mch-stack/build -r $recipes/mch/a100 -s $systems/balfrin -c ./cache.yaml -m $MOUNT
```
