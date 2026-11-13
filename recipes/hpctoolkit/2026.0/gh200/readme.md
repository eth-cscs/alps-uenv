# HPCToolkit's uenv

This uenv provides HPCToolkit/2026.0, an integrated suite of tools for measurement and analysis of program performance:
https://hpctoolkit.org/index.html

It has been built with Stackinator + Spack, using:
    - gcc/14.3.0
    - cuda/13.0.2
    - cray/mpich-9.1.0

There are different ways to use this uenv.

## Use case 1: single uenv

If the application code can be compiled using the available compilers/libraries in the uenv,
start compiling with:

```bash
uenv image pull hpctoolkit/2026.0
uenv start --view hpctoolkit hpctoolkit/2026.0
ls /user-tools/
```

then build the code using the default compiler versions:

```bash
mpicxx --version
    g++ (Spack GCC) 14.3.0
nvcc --version
    Cuda compilation tools, release 13.0, V13.0.88
```
    
then collect performance data by running a Slurm job with hpctoolkit, and generate a report as explained in the documentation:

```bash
srun hpcrun -e gpu=cuda -e PAPI_TOT_CYC -t build/test/performance/hilbert_perf_gpu
hpcstruct hpctoolkit-hilbert_perf_gpu-measurements-*
hpcprof hpctoolkit-hilbert_perf_gpu-measurements-*
# -> will create hpctoolkit-hilbert_perf_gpu-database-48561/
```

Eventually, transfer the performance database to your workstation, and look at the report with HPCToolkit\'s HPCViewer Graphical User Interface: https://hpctoolkit.org/download.html

## Use case 2: dual uenv

If the application code depends on another uenv, it is possible to load both uenvs with:

```bash
uenv start --help
uenv start lammps/20251210:v2,hpctoolkit/2026.0 --view=lammps:gpu,hpctoolkit:hpctoolkit
```

This will load both lammps (in /user-environment) and hpctoolkit (in /user-tools):

```bash
uenv status

    uenv  hpctoolkit
      mount  /user-tools
      views  [hpctoolkit]
    uenv  lammps
      mount  /user-environment
      views  [gpu]
```

Collect performance data by running a Slurm job with hpctoolkit, and generate a report as explained in the documentation:

```bash
srun hpcrun -e gpu=cuda -e PAPI_TOT_CYC \
    /user-environment/env/gpu/bin/lmp -sf gpu -pk gpu 1 -i lj_gpu.in

hpcstruct hpctoolkit-lmp-measurements-48569
hpcprof hpctoolkit-lmp-measurements-48569
# -> will create hpctoolkit-lmp-database-48569
```

Eventually, transfer the performance database to your workstation, and look at the report with HPCToolkit\'s HPCViewer Graphical User Interface: https://hpctoolkit.org/download.html
  
## Use case 3: build a custom uenv

If none of the above applies, it is possible to build a custom uenv, using https://eth-cscs.github.io/stackinator/
and the .yaml files in this directory.
