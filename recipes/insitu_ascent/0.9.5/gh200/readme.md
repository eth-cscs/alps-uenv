This uenv contains ascent/0.9.5 plus dependencies:

```
ascent/0.9.5-5tvprek
  camp-2025.03.0
  conduit-0.9.5
  occa-2.0
  raja-2025.03.2
  umpire-2025.09.0
  vtk-m-2.3.0

gcc/13.4.0-yrhdyox
cmake/3.31.8-ujwjqf3
cray-mpich/8.1.32-fvq4yfa
cuda/12.8.1-fel3gie
hdf5/1.14.6-q54kcdk
libfabric/1.22.0-sw5dkak
```

Changes to the packages in the common/repo directory are needed to build ascent/0.9.5

## Caveats

- Recipe is building fine with (gcc/12 or gcc/13) and (cuda/12.8.1 or cuda/12.6),
  but not with cuda@12.9.0:
    
```
> ascent/vtkh/filters/Slice.cpp
cub/device/dispatch/dispatch_transform.cuh(141): error: no operator "=" matches
these operands
```

## Ascent package.py variants

- default=False

```
    variant("adios2", default=False, description="Build Adios2 filter support")
    variant("babelflow", default=False, description="Build with BabelFlow")
    variant("caliper", default=False, description="Build Caliper support")
    variant("doc", default=False, description="Build Ascent's documentation")
    variant("dray", default=False, description="Build with Devil Ray support")
    variant("fides", default=False, description="Build Fides filter support")
    variant("mfem", default=False, description="Build MFEM filter support")
    variant("occa", default=False, description="Build with OCCA support")
    variant("openmp", default=(sys.platform != "darwin"), description="build openmp support")
    variant("python", default=False, description="Build Ascent Python support")
```

- default=True

```
    variant("blt_find_mpi", default=True, description="Use BLT CMake Find MPI logic")
    variant("fortran", default=True, description="Build Ascent Fortran support")
    variant("mpi", default=True, description="Build Ascent MPI Support")
    variant("raja", default=True, description="Build with RAJA support")
    variant("serial", default=True, description="build serial (non-mpi) libraries")
    variant("shared", default=True, description="Build Ascent as shared libs")
    variant("test", default=True, description="Enable Ascent unit tests")
    variant("umpire", default=True, description="Build with Umpire support")
    variant("vtkh", default=True, description="Build VTK-h filter and rendering support")

```

## spack spec ascent

```
 -   5tvprek  ascent@0.9.5~adios2~babelflow+blt_find_mpi~caliper+cuda~doc~dray~fides+fortran~ipo~mfem+mpi+occa+openmp~python+raja~rocm+serial+shared+test+umpire+vtkh build_system=cmake build_type=Debug commit=1c32d88b01439263cb4e473756a222824bb75abb cuda_arch:=90 generator=make arch=linux-sles15-neoverse_v2 %c,cxx,fortran=gcc@13.4.0
[+]  hcns3gf      ^compiler-wrapper@1.0 build_system=generic arch=linux-sles15-neoverse_v2
 -   a7vpsrc      ^conduit@0.9.5~adios+blt_find_mpi~caliper~doc~doxygen+examples+fortran+hdf5~hdf5_compat~ipo+mpi+parmetis~python+shared~silo+test+utilities~zfp build_system=cmake build_type=Release generator=make arch=linux-sles15-neoverse_v2 %c,cxx,fortran=gcc@13.4.0
 -   axfyvlz          ^blt@0.7.1 build_system=generic arch=linux-sles15-neoverse_v2 %c,cxx,fortran=gcc@13.4.0
 -   dmvqtxm          ^metis@5.1.0~gdb~int64~ipo~no_warning~real64+shared build_system=cmake build_type=Release generator=make patches:=4991da9,93a7903,b1225da arch=linux-sles15-neoverse_v2 %c,cxx=gcc@13.4.0
 -   lzvohkw          ^parmetis@4.0.3~gdb~int64~ipo+shared build_system=cmake build_type=Release generator=make patches:=4f89253,50ed208,704b84f arch=linux-sles15-neoverse_v2 %c,cxx=gcc@13.4.0
[e]  ojkkysu      ^gcc@13.4.0~binutils+bootstrap~graphite~mold~nvptx~piclibs~profiled~strip build_system=autotools build_type=RelWithDebInfo languages:='c,c++,fortran' arch=linux-sles15-neoverse_v2
 -   xg272x5      ^gcc-runtime@13.4.0 build_system=generic arch=linux-sles15-neoverse_v2
[e]  6lml6md      ^glibc@2.31 build_system=autotools arch=linux-sles15-neoverse_v2
 -   xbqccm4      ^gmake@4.4.1~guile build_system=generic arch=linux-sles15-neoverse_v2 %c=gcc@13.4.0
 -   njn4lhn      ^occa@2.0+cuda+opencl+openmp build_system=generic commit=3cba0841b2b87678da53e0b311cb7e162d781181 arch=linux-sles15-neoverse_v2 %c,cxx,fortran=gcc@13.4.0
 -   5zgb47i      ^raja@2025.03.2+cuda~desul+examples+exercises~gpu-profiling~ipo~lowopttest~omptarget~omptask+openmp~plugins~rocm~run-all-tests+shared~sycl~tests~vectorization build_system=cmake build_type=Release commit=6e36a94380adbe88fed11a3213fc08461428ece0 cuda_arch:=none generator=make arch=linux-sles15-neoverse_v2 %c,cxx=gcc@13.4.0
 -   esq7ggj          ^camp@2025.03.0+cuda~ipo~omptarget+openmp~rocm~sycl~tests build_system=cmake build_type=Release commit=ee0a3069a7ae72da8bcea63c06260fad34901d43 cuda_arch:=90 generator=make arch=linux-sles15-neoverse_v2 %c,cxx=gcc@13.4.0
 -   s2so3gr      ^umpire@2025.09.0~asan~backtrace+c+cuda~dev_benchmarks~device_alloc~deviceconst~examples+fmt_header_only~fortran~ipc_shmem~ipo+mpi~mpi3_shmem~numa~omptarget+openmp~rocm~sanitizer_tests~shared~sqlite_experimental~tools~werror build_system=cmake build_type=Release commit=6b0ea9edbbbc741c8a429768d946549cd3bd7d33 cuda_arch:=90 generator=make tests=none arch=linux-sles15-neoverse_v2 %c,cxx,fortran=gcc@13.4.0
 -   3of6ot2          ^fmt@11.0.2~ipo+pic~shared build_system=cmake build_type=Release cxxstd=11 generator=make arch=linux-sles15-neoverse_v2 %c,cxx=gcc@13.4.0
 -   we5bjy6      ^vtk-m@2.3.0~64bitids+cuda+cuda_native+doubleprecision+examples+fpic~ipo~kokkos~logging~mpi+openmp+rendering~rocm+shared~sycl~tbb~testlib build_system=cmake build_type=Release cuda_arch:=90 generator=make arch=linux-sles15-neoverse_v2 %c,cxx=gcc@13.4.0
 -   ujwjqf3  cmake@3.31.8~doc+ncurses+ownlibs~qtgui build_system=generic build_type=Release arch=linux-sles15-neoverse_v2 %c,cxx=gcc@13.4.0
 -   ump5h7g      ^curl@8.11.1~gssapi~ldap~libidn2~librtmp~libssh~libssh2+nghttp2 build_system=autotools libs:=shared,static tls:=openssl arch=linux-sles15-neoverse_v2 %c,cxx=gcc@13.4.0
[+]  3uhzjpc          ^gnuconfig@2024-07-27 build_system=generic arch=linux-sles15-neoverse_v2
 -   dijemen          ^nghttp2@1.65.0 build_system=autotools arch=linux-sles15-neoverse_v2 %c,cxx=gcc@13.4.0
 -   kjy6rnd              ^diffutils@3.10 build_system=autotools arch=linux-sles15-neoverse_v2 %c=gcc@13.4.0
 -   be4q7kp          ^openssl@3.4.1~docs+shared build_system=generic certs=mozilla arch=linux-sles15-neoverse_v2 %c,cxx=gcc@13.4.0
 -   6xotoz5              ^ca-certificates-mozilla@2025-05-20 build_system=generic arch=linux-sles15-neoverse_v2
 -   rslgx4m              ^perl@5.40.0+cpanm+opcode+open+shared+threads build_system=generic arch=linux-sles15-neoverse_v2 %c=gcc@13.4.0
 -   mjrjiqe                  ^berkeley-db@18.1.40+cxx~docs+stl build_system=autotools patches:=26090f4,b231fcc arch=linux-sles15-neoverse_v2 %c,cxx=gcc@13.4.0
 -   yg2ihbo                  ^bzip2@1.0.8~debug~pic+shared build_system=generic arch=linux-sles15-neoverse_v2 %c=gcc@13.4.0
 -   uvlfnrk                  ^gdbm@1.23 build_system=autotools arch=linux-sles15-neoverse_v2 %c=gcc@13.4.0
 -   7qxqaqd                      ^readline@8.2 build_system=autotools patches:=1ea4349,24f587b,3d9885e,5911a5b,622ba38,6c8adf8,758e2ec,79572ee,a177edc,bbf97f1,c7b45ff,e0013d9,e065038 arch=linux-sles15-neoverse_v2 %c=gcc@13.4.0
 -   ylrqsqn      ^ncurses@6.5~symlinks+termlib abi=none build_system=autotools patches:=7a351bc arch=linux-sles15-neoverse_v2 %c,cxx=gcc@13.4.0
 -   qwo3k2p      ^zlib-ng@2.2.4+compat+new_strategies+opt+pic+shared build_system=autotools arch=linux-sles15-neoverse_v2 %c,cxx=gcc@13.4.0
 -   fvq4yfa  cray-mpich@8.1.32+cuda~rocm build_system=generic arch=linux-sles15-neoverse_v2 %c,cxx,fortran=gcc@13.4.0
 -   25u7zwc      ^cray-gtl@8.1.32+cuda~rocm build_system=generic arch=linux-sles15-neoverse_v2
 -   qnhj4hv      ^cray-pmi@6.1.15 build_system=generic arch=linux-sles15-neoverse_v2
 -   nr3s7a5          ^cray-pals@1.3.2 build_system=generic arch=linux-sles15-neoverse_v2
 -   xiadyie      ^patchelf@0.17.2 build_system=autotools arch=linux-sles15-neoverse_v2 %c,cxx=gcc@13.4.0
[e]  v6kfem4      ^xpmem@2.9.6~kernel-module build_system=autotools arch=linux-sles15-neoverse_v2
 -   fel3gie  cuda@12.8.1~allow-unsupported-compilers~dev build_system=generic arch=linux-sles15-neoverse_v2
 -   7u3egbb      ^libxml2@2.13.5~http+pic~python+shared build_system=autotools arch=linux-sles15-neoverse_v2 %c=gcc@13.4.0
 -   p3s7wev          ^libiconv@1.18 build_system=autotools libs:=shared,static arch=linux-sles15-neoverse_v2 %c=gcc@13.4.0
 -   ugluk7w          ^xz@5.6.3~pic build_system=autotools libs:=shared,static arch=linux-sles15-neoverse_v2 %c=gcc@13.4.0
 -   q54kcdk  hdf5@1.14.6+cxx~fortran+hl~ipo~java~map+mpi+shared~subfiling~szip~threadsafe+tools api=default build_system=cmake build_type=Release generator=make arch=linux-sles15-neoverse_v2 %c,cxx=gcc@13.4.0
 -   mptd43o      ^pkgconf@2.3.0 build_system=autotools arch=linux-sles15-neoverse_v2 %c=gcc@13.4.0
[e]  sw5dkak  libfabric@1.22.0+cuda~debug~kdreg~level_zero~uring build_system=autotools cuda_arch:=90,90a fabrics:=cxi,rxd,rxm,shm,sockets,tcp,udp arch=linux-sles15-neoverse_v2
```
