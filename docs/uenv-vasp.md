# VASP

VASP (Vienna Ab initio Simulation Package) is a software package for performing ab initio quantum mechanical calculations.

> [!NOTE]
> VASP is only available to users with the appropriate license. Check the [VASP website](https://www.vasp.at/sign_in/registration_form/) for licensing.
> Contact the [CSCS service desk](https://support.cscs.ch/) for license verification. Once verified, users are added to the `vasp6` group, which allows access to prebuilt images and the source code.

## Accessing VASP images

!!! failure

    Describe access to images. Not yet finalized.

## Usage
The default build of vasp includes MPI, HDF5, Wannier90 and OpenACC (on GH200 and A100 architectures).
Start the uenv and load the `vasp` view:

```
uenv start ${path_to_vasp_image}
uenv view vasp
```
The `vasp_std`, `vasp_gam` and `vasp_ncl` executables are now available for use.

## Build from source
Start the uenv and load the `develop` view:
```
uenv start ${path_to_vasp_image}
uenv view develop
```
This will ensure that compiler executables are in `PATH`.
The appropriate makefile from the `arch` directory in the vasp source tree should be selected and link / include paths changed to use the `/user-environment/env/develop` prefix,
where all required dependencies can be found.
For example on GH200 and A100 architectures, select `makefile.include.nvhpc_omp_acc` and change the gpu flags to match the architecture. In this case `-gpu=cc60,cc70,cc80,cuda11.0` to `-gpu=cc80,cc90,cuda12.2` (depending on the included cuda version). After changing all include / link paths, compile VASP using make (only single thread build with is supported).


