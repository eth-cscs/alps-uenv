# NAMD

[NAMD] is a parallel molecular dynamics code based on [Charm++] designed for high-performance simulation of large biomolecular systems.

!!! danger "Licensing Terms and Conditions"
    
    [NAMD] is distributed free of charge for research purposes only and not for commercial use: users must agree to [NAMD license] in order to use it at [CSCS]. Users agree to acknowledge use of [NAMD] in any reports or publications of results obtained with the Software (see [NAMD Homepage] for details).

!!! warning

    Currently, we only provide single-GPU and single-node multi-GPU [NAMD] builds, which greatly benefit from the new GPU-resident mode providing very fast dynamics (see [NAME 3.0 new features]). If you require a multi-node version of [NAMD], please contact us.

## Single-node build

The single-node build works on a single node and benefits from the new GPU-resident mode (see [NAMD 3.0b6 GPU-Resident benchmarking results] for more details). The single-node build provides the following views:

* `namd-single-node` (standard view, with NAMD)
* `develop-single-node` (development view, without NAMD)

### Building from source

The [NAMD] `uenv` provides all the dependencies required to build [NAMD] from source. You can follow these steps to build [NAMD] from source:

```bash
export DEV_VIEW_NAME="develop-single-node"

# Start uenv and load develop view
uenv start <NAMD_UENV>
uenv view ${DEV_VIEW_NAME}

cd <PATH_TO_NAMD_SOURCE>

# Set variable VIEW_PATH to the view
export DEV_VIEW_PATH=/user-environment/env/${DEV_VIEW_NAME}

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

