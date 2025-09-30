This is the recipe to build ascent-0.9.5 and some dependencies:

```
gcc-13.4.0
cray-mpich-8.1.32
camp-2025.03.0
conduit-0.9.5
cuda-12.8.1
hdf5-1.14.6
raja-2025.03.0
umpire-2025.03.0
vtk-m-2.3.0
```

Packages in the common/repo are needed to build ascent/0.9.5

## Caveats

- Recipe is building fine with (gcc/12 or gcc/13) and (cuda/12.8.1 or cuda/12.6),
  but not with cuda@12.9.0:
    
```
> ascent/vtkh/filters/Slice.cpp
cub/device/dispatch/dispatch_transform.cuh(141): error: no operator "=" matches
these operands
```
