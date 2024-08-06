# NAMD

[NAMD] is a parallel molecular dynamics code based on [Charm++], designed for high-performance simulation of large biomolecular systems.

!!! danger "Licensing Terms and Conditions"
    
    [NAMD] is distributed free of charge for research purposes only and not for commercial use: users must agree to [NAMD license] in order to use it at [CSCS]. Users agree to acknowledge use of [NAMD] in any reports or publications of results obtained with the Software (see [NAMD Homepage] for details).

## Single-node build

The single-node build works on a single node and benefits from the new GPU-resident mode (see [NAMD 3.0b6 GPU-Resident benchmarking results] for more details). The single-node build provides the following views:

* `namd-single-node` (standard view, with NAMD)
* `develop-single-node` (development view, without NAMD)

### Building from source

!!! warning "TCL Version"
    According to the NAMD 3.0 release notes, TCL `8.6` is required. However, the source code for the `3.0` release still contains hard-coded
    flags for TCL `8.5`. The UENV provides `tcl@8.6`, therefore you need to manually modify NAMD 3.0's `arch/Linux-ARM64.tcl` file as follows:
    change `-ltcl8.5` to `-ltcl8.6` in the definition of the `TCLLIB` variable.

The [NAMD] `uenv` provides all the dependencies required to build [NAMD] from source. You can follow these steps to build [NAMD] from source:

```bash
export DEV_VIEW_NAME="develop-single-node"

# Start uenv and load develop view
uenv start <NAMD_UENV>
uenv view ${DEV_VIEW_NAME}

# Set variable VIEW_PATH to the view
export DEV_VIEW_PATH=/user-environment/env/${DEV_VIEW_NAME}

cd <PATH_TO_NAMD_SOURCE>

# ~~~~~
# Modify the "<PATH_TO_NAMD_SOURCE>/arch/Linux-ARM64.tcl" file now!
# Change "-ltcl8.5" with "-ltcl8.6" in the definition of the "TCLLIB" variable
# ~~~~~

# Build bundled Charm++
tar -xvf charm-8.0.0.tar && cd charm-8.0.0
./build charm++ multicore-linux-arm8 gcc --with-production --enable-tracing -j 32

# Configure NAMD build for GPU
cd .. 
./config Linux-ARM64-g++.cuda \
    --charm-arch multicore-linux-arm8-gcc --charm-base $PWD/charm-8.0.0 \
    --with-tcl --tcl-prefix ${DEV_VIEW_PATH} \
    --with-fftw --with-fftw3 --fftw-prefix ${DEV_VIEW_PATH} \
    --cuda-gencode arch=compute_90,code=sm_90 --with-single-node-cuda --with-cuda --cuda-prefix ${DEV_VIEW_PATH}
cd Linux-ARM64-g++.cuda && make -j 32

# !!! BEGIN OPTIONAL !!!
# Configure NAMD build for CPU
cd ..
./config Linux-ARM64-g++ \
    --charm-arch multicore-linux-arm8-gcc --charm-base $PWD/charm-8.0.0 \
    --with-tcl --tcl-prefix ${DEV_VIEW_PATH} \
    --with-fftw --with-fftw3 --fftw-prefix ${DEV_VIEW_PATH}
cd Linux-ARM64-g++ && make -j 32
# !!! END OPTIONAL !!!

cd ..
export LD_LIBRARY_PATH=${DEV_VIEW_PATH}/lib/

# Run NAMD (GPU version)
Linux-ARM64-g++.cuda/namd3 <NAMD_OPTIONS>

# !!! BEGIN OPTIONAL !!!
# Run NAMD (CPU version)
Linux-ARM64-g++/namd3 <NAMD_OPTIONS>
# !!! END OPTIONAL !!!
```

The optional section provides instructions on how to build a CPU-only build, should you need it (for constant pH MD simulations, for example).

## Multi-node build

The multi-node build works on multiple nodes and it is based on [Charm++] MPI backend. The multi-node build provides the following views:

* `namd`
* `develop` (development view, without NAMD)

!!! note "GPU-resident mode"
    The multi-node build based on [Charm++] MPI backend can't take advantage of the new GPU-resident mode. Unless you require the multi-node
    build or you can prove it is faster for your use case, we recommend using the single-node build with the GPU-resident mode.
    
### Building from source

!!! warning "TCL Version"
    According to the NAMD 3.0 release notes, TCL `8.6` is required. However, the source code for the `3.0` release still contains hard-coded
    flags for TCL `8.5`. The UENV provides `tcl@8.6`, therefore you need to manually modify NAMD 3.0's `arch/Linux-ARM64.tcl` file as follows:
    change `-ltcl8.5` to `-ltcl8.6` in the definition of the `TCLLIB` variable.

The [NAMD] `uenv` provides all the dependencies required to build [NAMD] from source. You can follow these steps to build [NAMD] from source:

```bash
export DEV_VIEW_NAME="develop"

# Start uenv and load develop view
uenv start <NAMD_UENV>
uenv view ${DEV_VIEW_NAME}

# Set variable VIEW_PATH to the view
export DEV_VIEW_PATH=/user-environment/env/${DEV_VIEW_NAME}

cd <PATH_TO_NAMD_SOURCE>

# ~~~~~
# Modify the "arch/Linux-ARM64.tcl" file now!
# Change "-ltcl8.5" with "-ltcl8.6" in the definition of the "TCLLIB" variable
# ~~~~~

# Build bundled Charm++
tar -xvf charm-8.0.0.tar && cd charm-8.0.0
env MPICXX=mpicxx ./build charm++ mpi-linux-arm8 smp --with-production -j 32

# Configure NAMD build for GPU
cd .. 
./config Linux-ARM64-g++.cuda \
    --charm-arch mpi-linux-arm8-smp --charm-base $PWD/charm-8.0.0 \
    --with-tcl --tcl-prefix ${DEV_VIEW_PATH} \
    --with-fftw --with-fftw3 --fftw-prefix ${DEV_VIEW_PATH} \
    --cuda-gencode arch=compute_90,code=sm_90 --with-single-node-cuda --with-cuda --cuda-prefix ${DEV_VIEW_PATH}
cd Linux-ARM64-g++.cuda && make -j 32

# !!! BEGIN OPTIONAL !!!
# Configure NAMD build for CPU
cd ..
./config Linux-ARM64-g++ \
    --charm-arch mpi-linux-arm8-smp --charm-base $PWD/charm-8.0.0 \
    --with-tcl --tcl-prefix ${DEV_VIEW_PATH} \
    --with-fftw --with-fftw3 --fftw-prefix ${DEV_VIEW_PATH}
cd Linux-ARM64-g++ && make -j 32
# !!! END OPTIONAL !!!

cd ..
export LD_LIBRARY_PATH=${DEV_VIEW_PATH}/lib/

# Run NAMD (GPU version)
Linux-ARM64-g++.cuda/namd3 <NAMD_OPTIONS>

# !!! BEGIN OPTIONAL !!!
# Run NAMD (CPU version)
Linux-ARM64-g++/namd3 <NAMD_OPTIONS>
# !!! END OPTIONAL !!!
```

The optional section provides instructions on how to build a CPU-only build, should you need it (for constant pH MD simulations, for example).

## Useful Links

* [NAMD Spack package]
* [NAMD Tutorials]
* [Charm++ Spack package]
* [Running Charm++ Programs]
* [What you should know about NAMD and Charm++ but were hoping to ignore] by J. C. Phillips

[Charm++]: https://charm.cs.uiuc.edu/ 
[Charm++ Spack package]: https://packages.spack.io/package.html?name=charmpp 
[CSCS]: https://www.cscs.ch
[NAMD]: http://www.ks.uiuc.edu/Research/namd/
[NAMD Homepage]: http://www.ks.uiuc.edu/Research/namd/
[NAMD license]: http://www.ks.uiuc.edu/Research/namd/license.html
[NAMD Tutorials]: http://www.ks.uiuc.edu/Training/Tutorials/index.html#namd
[NAMD Spack package]: https://packages.spack.io/package.html?name=namd
[Running Charm++ Programs]: https://charm.readthedocs.io/en/latest/charm++/manual.html#running-charm-programs
[What you should know about NAMD and Charm++ but were hoping to ignore]: https://dl.acm.org/doi/pdf/10.1145/3219104.3219134
[NAMD 3.0 new features]: https://www.ks.uiuc.edu/Research/namd/3.0/features.html
[NAMD 3.0b6 GPU-Resident benchmarking results]: https://www.ks.uiuc.edu/Research/namd/benchmarks/

