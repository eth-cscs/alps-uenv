The `netcdf_fortran` package was added to repo to fix compilation when using a mixed compiler toolchain.

The problem (`when %gcc` instead of `when %fortran=nvhpc`) has been fixed in spack-packages, and will be available in release 25.08.
