# LAMMPS

[LAMMPS] is a classical molecular dynamics code with a focus on materials modeling. It's an acronym for Large-scale Atomic/Molecular Massively Parallel Simulator. LAMMPS has potentials for solid-state materials (metals, semiconductors) and soft matter (biomolecules, polymers) and coarse-grained or mesoscopic systems. It can be used to model atoms or, more generically, as a parallel particle simulator at the atomic, meso, or continuum scale. See [LAMMPS Features] for a detailed overview.

## Running

We provide two versions of LAMMPS, one with the kokkos package enabled, and one with the GPU packaged enabled. These can be loaded as follows:
```bash
uenv start --view kokkos <LAMMPS_UENV>
```

or

```bash
uenv start --view gpu <LAMMPS_UENV>
```

!!! warning
    [LAMMPS] is built with GPU-aware MPI. Make sure to set `MPICH_GPU_SUPPORT_ENABLED=1` when running [LAMMPS].

## Building from source

The [LAMMPS] `uenv` provides all the dependencies required to build [LAMMPS] from source. You can follow these steps to build [LAMMPS] from source:

```bash
# Start uenv and load develop view
uenv start --view develop-kokkos <LAMMPS_UENV> # or uenv start --view develop-gpu <LAMMPS_UENV>, if building using the GPU package

# cd to LAMMPS source directory
cd <PATH_TO_LAMMPS_SOURCE>

# CMake
mkdir build && cd build
cmake -C ../cmake/presets/kokkos-cuda.cmake ../cmake/  -DKokkos_ENABLE_IMPL_CUDA_MALLOC_ASYNC=OFF -DKokkos_ARCH_NATIVE=ON -DKokkos_ARCH_HOPPER90=ON -DKokkos_ARCH_PASCAL60=OFF

cmake --build . --parallel 32
```

[LAMMPS]: https://www.lammps.org/
[LAMMPS Features]: https://docs.lammps.org/Intro_features.html

