# VASP

VASP (Vienna Ab initio Simulation Package) is a software package for performing ab initio quantum mechanical calculations.

> [!NOTE]
> VASP is only available to users with the appropriate license. Check the [VASP website](https://www.vasp.at/sign_in/registration_form/) for licensing.
> Contact the [CSCS service desk](https://support.cscs.ch/) for license verification. Once verified, users are added to the `vasp6` group, which allows access to prebuilt images and the source code.


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
