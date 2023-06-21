The software stacks for MCH.

Changes from the v4 stack installed on Balfrin:
- build using stackinator instead of Makefiles: https://github.com/eth-cscs/spack-stack
- upgrade from a Spack `v0.19-dev` commit to the `releases/v0.20` branch.
- upgrade cray-mpich from `v8.1.18.4` to `v8.1.25` for the gcc programming environment
    - see the MPI version table in the [Stackinator docs](https://eth-cscs.github.io/stackinator/recipes/#mpi) for more information.

