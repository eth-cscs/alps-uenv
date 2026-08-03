# omp-offload uenv

A uenv that provides two compiler toolchains with **OpenMP offload to NVIDIA
GH200 (Hopper, cc 9.0)** GPUs:

- **nvhpc @26.3** — `nvc` / `nvc++` / `nvfortran` (offload via `-mp=gpu` and OpenACC)
- **gcc @15.3 `+nvptx`** — `gcc` / `g++` / `gfortran` (offload via `-fopenmp -foffload=nvptx-none`)

plus cray-mpich (`+cuda`), CUDA 13.3, nvpl BLAS/LAPACK, FFTW, NCCL and the usual
build tools. Built with Stackinator + Spack; based on the `prgenv-nvfortran`
template.

The environment is exposed through a filesystem view named **`nvfort`**.

```bash
# interactive
uenv start ./store.squashfs
uenv view nvfort
# or run a single command
uenv run --view=nvfort ./store.squashfs -- <command>
```

---

## 1. What is custom in this recipe

Getting `gcc +nvptx` to build *and* to actually offload inside a uenv required
three fixes. Two live in a custom gcc package (`repo/packages/gcc/`), the third
is a post-install hook (`post-install`). nvhpc needs no customisation.

### a. gcc nvptx target arch — `repo/packages/gcc/package.py`

GCC's nvptx offload compiler has a narrow window of valid GPU targets on this
system, and the stock package picks a value outside it:

- **CUDA 13.3's `ptxas` floor is `sm_75`** — it rejects every arch below it.
- **gcc 15's nvptx backend ceiling is `sm_89`** — `sm_90` is rejected at
  `configure` (`Unknown arch used in --with-arch=sm_90`). No GCC release has a
  Hopper (`sm_90`) nvptx target yet. This is why the naive "just use `sm_90`"
  advice is **wrong**.

gcc emits PTX and the CUDA driver JIT-compiles it forward-compatibly, so
**`sm_80` PTX runs fine, JIT'd, on the GH200**. The package is patched to target
`sm_80` in the two places gcc would otherwise fall back to `sm_52` (which
`ptxas` rejects, breaking the build):

- `nvptx_install()` configures the offload compiler with
  `--with-arch=sm_80 --with-multilib-list=sm_80` (a single `sm_80` multilib;
  without the multilib flag gcc also builds an `sm_52` one).
- A `patch()` step `filter_file`s `gcc/config.gcc` so
  `nvptx_multilibs_default` and the `with_arch` fallback are `sm_80`, not
  `sm_52` — this stops the *host* offload build (which we can't pass configure
  flags to) from re-introducing an `sm_52` multilib.

> To build a single image that targets several GPUs, widen the multilib list to
> any set within `[sm_75, sm_89]`, e.g. `--with-multilib-list=sm_75,sm_80,sm_89`.

### b. Idempotent `libgomp.spec` rewrite — `repo/packages/gcc/package.py`

Spack's gcc package post-processes `lib64/libgomp.spec` to embed an rpath. The
upstream code edits the file in place and is **not idempotent**. Because
Stackinator builds gcc, pushes it to the build cache, and then reinstalls it
from the cache, the post-install step runs twice — duplicating the injected
block and producing a run of **three consecutive blank lines**. gcc's own spec
parser bails on that (`fatal error: specs file malformed after 157 characters`),
which **breaks all `-fopenmp` linking** — host and GPU alike.

The fix (in `write_specs_file()`): keep a pristine `libgomp.spec.orig` created
only on the first run, then always regenerate `libgomp.spec` from it with a
truncating write. The result is byte-identical no matter how many times the
step runs.

### c. Exposing gcc's offload toolchain in the view — `post-install`

gcc's offload tools are not surfaced by the Spack filesystem view, so even a
correctly built compiler fails at offload time:

- `mkoffload` spawns `…-accel-nvptx-none-gcc` / `nvptx-none-as` via `PATH`, and
  they live in `<gcc-prefix>/bin` (not the view `bin`) →
  `mkoffload: fatal error: posix_spawnp: No such file or directory`.
- the runtime plugin `libgomp-plugin-nvptx.so.1` lives in `<gcc-prefix>/lib64`
  (not on the view's `LD_LIBRARY_PATH`) → `num_devices = 0` at run time.

The `post-install` hook (run by Stackinator after `env-meta`, before the
squashfs is created) resolves the concrete gcc prefix with
`spack find --format "{prefix}" "gcc@15 +nvptx"` and injects
`<gcc-prefix>/bin` into `PATH` and `<gcc-prefix>/lib64` into `LD_LIBRARY_PATH`
for every view in `meta/env.json` (idempotently). This is why `gcc` offload
works out of the box from the `nvfort` view, with no manual `PATH` /
`LD_LIBRARY_PATH` / `-B` fiddling.

---

## 2. Using the uenv to compile offload codes

All examples assume the `nvfort` view is active (either via
`uenv run --view=nvfort ./store.squashfs -- …` or an interactive
`uenv start` + `uenv view nvfort`).

Set `OMP_TARGET_OFFLOAD=MANDATORY` when you want the program to **fail loudly**
instead of silently falling back to the host if the GPU isn't used — handy for
verifying that offload really happened.

### gcc / gfortran (nvptx offload)

The key flags are `-fopenmp` **and** `-foffload=nvptx-none`.

```bash
# C
gcc  -fopenmp -foffload=nvptx-none -O2 prog.c   -o prog

# C++
g++  -fopenmp -foffload=nvptx-none -O2 prog.cpp -o prog

# Fortran
gfortran -fopenmp -foffload=nvptx-none -O2 prog.f90 -o prog

# run (forces offload; errors out if it can't reach the GPU)
OMP_TARGET_OFFLOAD=MANDATORY ./prog
```

The target arch is baked into the compiler (`sm_80`, JIT'd onto the GH200) — you
do **not** pass a `-march`/`cc90` flag to gcc.

Minimal C example (`offload.c`):

```c
#include <stdio.h>
#include <stdlib.h>
#include <omp.h>

int main(void) {
    int n = 1 << 20;
    double *a = malloc(n * sizeof(double));
    int on_gpu = 0;

    #pragma omp target teams distribute parallel for \
                map(from:a[0:n]) map(tofrom:on_gpu)
    for (int i = 0; i < n; i++) {
        a[i] = 2.0 * i;
        if (i == 0) on_gpu = !omp_is_initial_device();
    }
    printf("num_devices=%d ran_on_gpu=%d\n", omp_get_num_devices(), on_gpu);
    return 0;
}
```

```bash
gcc -fopenmp -foffload=nvptx-none -O2 offload.c -o offload
OMP_TARGET_OFFLOAD=MANDATORY ./offload
# -> num_devices=4 ran_on_gpu=1
```

### nvfortran / nvc / nvc++ (nvhpc offload)

nvhpc offloads with `-mp=gpu`; select the GH200 arch with `-gpu=cc90`.

```bash
# OpenMP offload
nvfortran -mp=gpu -gpu=cc90 -O2 prog.f90 -o prog
nvc       -mp=gpu -gpu=cc90 -O2 prog.c   -o prog
nvc++     -mp=gpu -gpu=cc90 -O2 prog.cpp -o prog

# OpenACC offload
nvc       -acc   -gpu=cc90 -O2 prog.c   -o prog

OMP_TARGET_OFFLOAD=MANDATORY ./prog
```

Minimal Fortran example (`offload.f90`, works with both `gfortran` and
`nvfortran`):

```fortran
program p
  use omp_lib
  integer, parameter :: n = 1048576
  real(8), allocatable :: a(:)
  integer :: i
  logical :: gpu = .false.
  allocate(a(n))
  !$omp target teams distribute parallel do map(from:a) map(tofrom:gpu)
  do i = 1, n
    a(i) = 2.0d0 * i
    if (i == 1) gpu = .not. omp_is_initial_device()
  end do
  print *, 'ndev=', omp_get_num_devices(), ' gpu=', gpu
end program
```

```bash
# with gcc
gfortran  -fopenmp -foffload=nvptx-none -O2 offload.f90 -o off_gcc
# with nvhpc
nvfortran -mp=gpu -gpu=cc90            -O2 offload.f90 -o off_nv

OMP_TARGET_OFFLOAD=MANDATORY ./off_gcc
OMP_TARGET_OFFLOAD=MANDATORY ./off_nv
```

### MPI + offload

`mpicc` / `mpif90` (cray-mpich, CUDA-aware) wrap the nvhpc compilers by default;
combine the offload flags as above, e.g.:

```bash
mpicc  -mp=gpu -gpu=cc90 -O2 prog.c   -o prog
mpif90 -mp=gpu -gpu=cc90 -O2 prog.f90 -o prog
```
