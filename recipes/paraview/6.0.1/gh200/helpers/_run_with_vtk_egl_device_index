#!/bin/bash

GPUS=(3 2 1 0)
let lrank=$SLURM_LOCALID%4
export VTK_DEFAULT_EGL_DEVICE_INDEX=${GPUS[lrank]}

exec $*
