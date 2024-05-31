# GROMACS

GROMACS (GROningen Machine for Chemical Simulations) is a versatile and widely-used open source package to perform molecular dynamics, i.e. simulate the Newtonian equations of motion for systems with hundreds to millions of particles.
It is primarily designed for biochemical molecules like proteins, lipids and nucleic acids that have a lot of complicated bonded interactions, but since GROMACS is extremely fast at calculating the nonbonded interactions (that usually dominate simulations) many groups are also using it for research on non-biological systems, e.g. polymers.

!!! danger "Licensing Terms and Conditions"
    
    GROMACS is a joint effort, with contributions from developers around the world: users agree to acknowledge use of GROMACS in any reports or publications of results obtained with the Software (see [GROMACS Homepage] for details).

## ALPS (GH200)

### Setup

On ALPS, we provide pre-built user environments containing GROMACS alongside all the required dependencies for the GH200 hardware setup. To access the `gmx_mpi` executable, we do the following:

```bash
uenv image pull       # exact command TBD
uenv start ...        # exact command TBD

uenv view gromacs     # load the gromacs view
gmx_mpi --version     # check GROMACS version
```

The images also provide two alternative views, namely `plumed` and `develop`.
After starting the pulled image using `uenv start ...`, one may do the following see the available views.

```bash
$ uenv status
/user-environment:gromacs-gh200
  GPU-optimised GROMACS with and without PLUMED, and the toolchain to build your own GROMACS.
  modules: no modules available
  views:
    develop
    gromacs
    plumed
```

The `develop` view has all the required dependencies or GROMACS without the program itself. This is meant for those users who want to use a customized variant of GROMACS for their simulation which they build from source. This view makes it convenient for users as it provides the required compilers (GCC 12), CMake, CUDA, hwloc, Cray MPICH, among many others which their GROMACS can use during build and installation. Users must enable this view each time they want to use their custom GROMACS installation.

The `plumed` view contains GROMACS 2022.5 (older version) with PLUMED 2.9.0. This is due to the compatibility requirements of PLUMED. CSCS will periodically update these user environment images to feature newer versions as they are made available.

The `gromacs` view contains the newest GROMACS 2024.1 that has been configured and tested for the highest performance on the Grace-Hopper nodes.

### How to Run

To start a job, 2 bash scripts are required: a standard SLURM submission script, and a wrapper to start the CUDA MPS daemon (in order to have multiple MPI ranks per GPU).

The CUDA MPS wrapper here:
```bash
#!/bin/bash
# Example mps-wrapper.sh usage:
# > srun [...] mps-wrapper.sh -- <cmd>

TEMP=$(getopt -o '' -- "$@")
eval set -- "$TEMP"

# Now go through all the options
while true; do
    case "$1" in
        --)
            shift
            break
            ;;
        *)
            echo "Internal error! $1"
            exit 1
            ;;
    esac
done

set -u

export CUDA_MPS_PIPE_DIRECTORY=/tmp/nvidia-mps
export CUDA_MPS_LOG_DIRECTORY=/tmp/nvidia-log
# Launch MPS from a single rank per node
if [ $SLURM_LOCALID -eq 0 ]; then
    CUDA_VISIBLE_DEVICES=0,1,2,3 nvidia-cuda-mps-control -d
fi
# Wait for MPS to start sleep 5
sleep 5

exec "$@"
```

The wrapper script above can be made executable with `chmod +x mps-wrapper.sh`.
The SLURM submission script can be adapted from the template below to use the application and the `mps-wrapper.sh` in conjunction.

```bash
#!/bin/bash

#SBATCH --job-name="JOB NAME"
#SBATCH --nodes=1             # number of GH200 nodes with each node having 4 CPU+GPU
#SBATCH --ntasks-per-node=8   # 8 MPI ranks per node
#SBATCH --cpus-per-task 32    # 32 OMP threads per MPI rank
#SBATCH --account=ACCOUNT
#SBATCH --hint=nomultithread  

export MPICH_GPU_SUPPORT_ENABLED=1

export GMX_GPU_DD_COMMS=true
export GMX_GPU_PME_PP_COMMS=true
export GMX_FORCE_UPDATE_DEFAULT_GPU=true
export GMX_ENABLE_DIRECT_GPU_COMM=1
export GMX_FORCE_GPU_AWARE_MPI=1

srun ./mps-wrapper.sh -- gmx_mpi mdrun -s input.tpr -ntomp 32 -bonded gpu -nb gpu -pme gpu -pin on -v -noconfout -dlb yes -nstlist 300 -gpu_id 0123 -npme 1 -nsteps 10000 -update gpu
```

This can be run using `sbatch launch.sbatch` on the login node with the user environment loaded.

This submission script is only representative. Users must run their input files with a range of parameters to find an optimal set for the production runs. Some hints for this exploration below:

!!! info "Configuration Hints"

    - Each Grace CPU has 72 cores, but a small number of them are used for the underlying processes such as runtime daemons. So all 72 cores are not available for compute. To be safe, do not exceed more than 64 OpenMP threads on a single CPU even if it leads to a handful of cores idling.
    - Each node has 4 Grace CPUs and 4 Hopper GPUs. When running 8 MPI ranks (meaning two per CPU), keep in mind to not ask for more than 32 OpenMP threads per rank. That way no more than 64 threads will be running on a single CPU.
    - Try running both 64 OMP threads x 1 MPI rank and 32 OMP threads x 2 MPI ranks configurations for the test problems and pick the one giving better performance. While using multiple GPUs, the latter can be faster by 5-10%.
    - `-update gpu`  may not be possible for problems that require constraints on all atoms. In such cases, the update (integration) step will be performed on the CPU. This can lead to performance loss of at least 10% on a single GPU. Due to the overheads of additional data transfers on each step, this will also lead to lower scaling performance on multiple GPUs.
    - When running on a single GPU, one can either configure the simulation with 1-2 MPI ranks with `-gpu_id`  as `0` , or try running the simulation with a small number of parameters and let GROMACS run with defaults/inferred parameters with a command like the following in the SLURM script:
    `srun ./mps-wrapper.sh -- gmx_mpi mdrun -s input.tpr -ntomp 64` 
    - Given the compute throughput of each Grace-Hopper module (single CPU+GPU), **for smaller-sized problems, it is possible that a single-GPU run is the fastest**. This may happen when the overheads of communication and orchestration exceed the benefits of parallelism across multiple GPUs. In our test cases, a single Grace-Hopper module has consistently shown a 6-8x performance speedup over a single node on Piz Daint.

!!! warning "Known Performance/Scaling Issues"

    - The current build of GROMACS on our system allows **only one MPI rank to be dedicated for PME** with `-nmpe 1`. This becomes a serious performance limitation for larger systems where the non-PME ranks finish their work before the PME rank leading to unwanted load imbalances across ranks. This limitation is targeted to be fixed in the subsequent releases of our builds of user environments.
    - The above problem is especially critical for large problem sizes (1+ million atom systems) but is far less apparent in small and medium sized runs.
    - If the problem allows the integration step to take place on the GPU with `-update gpu`, that can lead to significant performance and scaling gains as it allows an even greater part of the computations to take place on the GPU.
    - SLURM and CUDA MPS configurations are being explored to extend the simulation beyond a single compute node (of 4 CPUs+GPUs). Documentation will be updated once scaling across nodes is reliably reproduced. As of now, **simulations are recommended to be contained to a single node**.

[GROMACS Homepage]: https://www.gromacs.org