#!/bin/bash

# select_cpu_device wrapper script
GPUS=(3 2 1 0)
let lrank=$SLURM_LOCALID%4
export VTK_DEFAULT_EGL_DEVICE_INDEX=${GPUS[lrank]}

export LD_LIBRARY_PATH=@PV_LIBRARY_PATH@:$LD_LIBRARY_PATH

exec $*
