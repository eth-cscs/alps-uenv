This is the recipe to build ascent-0.9.5 and some dependencies:

```
camp-2025.03.0
conduit-0.9.5
cray-mpich
cuda-12.8.1
gcc-13.4.0
hdf5-1.14.6
raja-2025.03.0
umpire-2025.03.0
vtk-m-2.3.0
```

## Caveats

- Recipe is building fine with gcc/12 or gcc/13 and cuda@12.8.1, but not with
  cuda@12.9.0:
    
```
> ascent/vtkh/filters/Slice.cpp
cub/device/dispatch/dispatch_transform.cuh(141): error: no operator "=" matches
these operands
```
