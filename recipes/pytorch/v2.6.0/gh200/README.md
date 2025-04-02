# PyTorch 2.6

This `uenv` recipe was designed with the intention of being able to run
`Megatron-LM` based pre-training workloads out of the box. Thus, it comes with
batteries included and does not just provide the bare `PyTorch` framework. The
recipe is based on `spack`'s latest stable release `v0.23.1`. Thus, many
packages had to be backported in order to achieve compatibility with
`PyTorch@2.6` and `python@13`.

## Package Updates

The following packages have been updated manually. The reasons are varied, but
include for example
- fixes to make `spack.build_systems.python` work by fully qualifying the name
- patches to make packages compatible with `python@13`
- upgrades to `py-torch@2.6`

Many of the changes are taken from the spack `develop` branch and will likely
land in the next version. However, there are also some fixes with are not
upstreamed (yet).

### nccl
- new versions

### aws-ofi-nccl
- new versions

### hdf5
- added new variant `direct-vfd` to enable `O_DIRECT` virtual file driver

### faiss
- fix `python` error: import `build_systems` module from `spack` and use
  qualified `build_systems.python`

### nvtx
- fix `python` error: import `build_systems` module from `spack` and use
  qualified `build_systems.python`

### py-cython
- pulled from `develop` to support `python@13`
- see https://github.com/spack/spack/pull/47714

### py-sympy
- upgraded to version 1.13.1
- needed for `py-torch`, see https://github.com/spack/spack/pull/48951

### py-torch
- upgraded to 2.6.0 using https://github.com/spack/spack/pull/48794
    - dependencies updated
    - use system `nvtx` library
    - patch for `gloo`
    - patch for `xnnpack` on `aarch64`
    - requires updating
        - `cpuinfo` (new version)
        - `py-pybind11` (new version)
        - `py-torch-nvidia-apex` (version deprecation, patches)
        - `py-torchaudio` (new version)
        - `py-torchvision` (new version)
- enabled built-in flash attention

### py-torch-nvidia-apex
- version update (see `py-torch`)
- refactoring of variants
- enabled submodules (needed for cutlass)

### sentencepiece
- version update
- disable `TCMalloc` (added variant set to false by default) because of runtime
  errors

### py-sentencepiece
- version update

### py-sentry-sdk
- version update
- `pypi` naming scheme changed
    - underscore instead of hyphen in tar filename but not folder (why???)
    - `sentry-sdk/sentry-sdk-0.17.6.tar.gz` vs
      `sentry-sdk/sentry_sdk-2.0.0.tar.gz`

### py-triton
- new versions are no longer tagged and `pypi` does not provide source
  distributions: added commit hashes based on commit logs
- refactoring of dependencies
- patch usage of `bdist_wheel`: is part of `setuptools` in more recent versions
  instead `pypa`
- set environment variables:
    - force triton to use system `cuda` libraries and system `pybind11`
    - make a temporary triton home directory for downloads
    - `MAX_JOBS` for number build jobs
- define new `PythonPipBuilder` class which builds from top level directory
    - starting the build process from the `python` subdirectory causes errors
    - `spack` does not provide an option to specify this in the `PythonPackage`
        - if you define the `build_directory`, it will change directories
          instead of adding the directory as last argument to `pip`

### py-transformer-engine
- refactored dependencies
- added `cudnn` dependency
- set environment variables
    - force system `cudnn`
    - set `CUDAARCHS`
- patch to allow `python@13`

### py-zarr
- update version, see https://github.com/spack/spack/pull/48786
    - requires new package: `py-donfig`
    - requires new version of `py-numcodecs`

### py-tokenizers
- update version

### py-huggingface-hub
- update version, see https://github.com/spack/spack/pull/47600
    - new variant `hf` requires new package `py-hf-transfer`

### py-transformers
- update version

### py-pydantic, py-pydantic-core
- update version, see https://github.com/spack/spack/pull/47771
- needed for `python@13`

### py-safetensors
- update version, see https://github.com/spack/spack/pull/47774
- needed for `python@13`

### py-wandb
- new versions: I failed to build from source using `spack`
- old versions: don't work with recent `numpy`
- requires patching `py-dockerpy-creds` in all cases
- installed by getting the wheel from pypi, see
  https://github.com/spack/spack/pull/44908

### py-dockerpy-creds
- umaintained, needs patch to fix `distutils` in newer python versions, see
  https://github.com/shin-/dockerpy-creds/pull/15
- needed by `py-wandb`

### py-trove-classifiers
- version bump
- includes more recently introduced classifiers
- needed for py-wandb

### py-psutil
- version bump
- needed for running py-wandb

## Full Diff w.r.t. v0.23.1

    diff --git c/var/spack/repos/builtin/packages/aws-ofi-nccl/package.py i/var/spack/repos/builtin/packages/aws-ofi-nccl/package.py
    index adb7474869..30f8b62e77 100644
    --- c/var/spack/repos/builtin/packages/aws-ofi-nccl/package.py
    +++ i/var/spack/repos/builtin/packages/aws-ofi-nccl/package.py
    @@ -18,6 +18,16 @@ class AwsOfiNccl(AutotoolsPackage):
         maintainers("bvanessen")
     
         version("master", branch="master")
    +    version("1.14.0", sha256="0420998e79a8ec0db0541bcc1f09f4a94c4c75fd1c096a4ef0507a0e8f2d540c")
    +    version("1.13.0", sha256="50dd231a0a99cec29300df46b8e828139ced15322a3c3c41b1d22dcc9a62ec02")
    +    version("1.12.1", sha256="821f0929c016e5448785bbc6795af5096559ecfc6c9479eb3818cafa61424576")
    +    version("1.12.0", sha256="93029207103b75f4dc15f023b3b8692851202b52b7e2824723dd5d328f0ea65b")
    +    version("1.11.1", sha256="a300e620e03ba3cc0915f9d466232ff0bf6c84edf4e2cd93592d53cf2a62741b")
    +    version("1.11.0", sha256="45d935133b183c945c16b70d8428d676a554faf5bd922b7909e9f1ec55ba6168")
    +    version("1.10.0", sha256="ed63f627b42c7b0f7312ce2916a3c4dfeb5145f78b492c0d1e0d0a6828a0474c")
    +    version("1.9.2", sha256="f763771e511ae3bc7bb708795f9802867a4a2bc4e4df6a265c7f6a033e9a8b9a")
    +    version("1.9.1", sha256="3ee01258674e70d6966eb6d319461f9b882afae618e217e0ae7ec03d26169b35")
    +    version("1.9.0", sha256="8d6d0469110a89b5431836d263860fb60fde7beccb26f553de41dca1feb61b51")
         version("1.8.1", sha256="beb59959be0f60b891f9549f4df51b394e97e739416c88c3436e75516fe067c8")
         version("1.8.0", sha256="a2f1750d4908924985335e513186353d0c4d9a5d27b1a759f6aa31a10e74c06d")
         version("1.7.4", sha256="472bbc977ce37d0cf9239b8e366f4f247226a984eb8c487aadd884af53f00e13")
    diff --git c/var/spack/repos/builtin/packages/cpuinfo/package.py i/var/spack/repos/builtin/packages/cpuinfo/package.py
    index 2a3e905be0..7f8da272f7 100644
    --- c/var/spack/repos/builtin/packages/cpuinfo/package.py
    +++ i/var/spack/repos/builtin/packages/cpuinfo/package.py
    @@ -19,6 +19,7 @@ class Cpuinfo(CMakePackage):
         license("BSD-2-Clause")
     
         version("main", branch="main")
    +    version("2024-09-26", commit="1e83a2fdd3102f65c6f1fb602c1b320486218a99")  # py-torch@2.6:
         version("2024-09-06", commit="094fc30b9256f54dad5ad23bcbfb5de74781422f")  # py-torch@2.5.1:
         version("2024-08-30", commit="fa1c679da8d19e1d87f20175ae1ec10995cd3dd3")  # py-torch@2.5.0
         version("2023-11-04", commit="d6860c477c99f1fce9e28eb206891af3c0e1a1d7")  # py-torch@2.3:2.4
    diff --git c/var/spack/repos/builtin/packages/faiss/package.py i/var/spack/repos/builtin/packages/faiss/package.py
    index ceb57a874e..711e0bb1b5 100644
    --- c/var/spack/repos/builtin/packages/faiss/package.py
    +++ i/var/spack/repos/builtin/packages/faiss/package.py
    @@ -5,6 +5,7 @@
     
     import os
     
    +from spack import build_systems
     from spack.build_systems import autotools, cmake, python
     from spack.package import *
     
    @@ -114,9 +115,9 @@ def install(self, pkg, spec, prefix):
             super().install(pkg, spec, prefix)
             if spec.satisfies("+python"):
     
    -            class CustomPythonPipBuilder(python.PythonPipBuilder):
    +            class CustomPythonPipBuilder(build_systems.python.PythonPipBuilder):
                     def __init__(self, pkg, build_dirname):
    -                    python.PythonPipBuilder.__init__(self, pkg)
    +                    build_systems.python.PythonPipBuilder.__init__(self, pkg)
                         self.build_dirname = build_dirname
     
                     @property
    diff --git c/var/spack/repos/builtin/packages/hdf5/package.py i/var/spack/repos/builtin/packages/hdf5/package.py
    index 12e99d9bf6..c1e0d2982a 100644
    --- c/var/spack/repos/builtin/packages/hdf5/package.py
    +++ i/var/spack/repos/builtin/packages/hdf5/package.py
    @@ -121,6 +121,7 @@ class Hdf5(CMakePackage):
         variant(
             "subfiling", when="@1.14: +mpi", default=False, description="Enable Subfiling VFD support"
         )
    +    variant("direct-vfd", default=False, description="Enable O_DIRECT virtual file driver")
         variant("fortran", default=False, description="Enable Fortran support")
         variant("java", when="@1.10:", default=False, description="Enable Java support")
         variant("threadsafe", default=False, description="Enable thread-safe capabilities")
    diff --git c/var/spack/repos/builtin/packages/libfuse/fix_aarch64_compile.patch i/var/spack/repos/builtin/packages/libfuse/fix_aarch64_compile.patch
    new file mode 100644
    index 0000000000..0e1acef3a4
    --- /dev/null
    +++ i/var/spack/repos/builtin/packages/libfuse/fix_aarch64_compile.patch
    @@ -0,0 +1,635 @@
    +diff --git a/include/fuse_kernel.h b/include/fuse_kernel.h
    +index c632b58..c0ef981 100644
    +--- a/include/fuse_kernel.h
    ++++ b/include/fuse_kernel.h
    +@@ -88,12 +88,11 @@
    + #ifndef _LINUX_FUSE_H
    + #define _LINUX_FUSE_H
    + 
    +-#include <sys/types.h>
    +-#define __u64 uint64_t
    +-#define __s64 int64_t
    +-#define __u32 uint32_t
    +-#define __s32 int32_t
    +-#define __u16 uint16_t
    ++#ifdef __KERNEL__
    ++#include <linux/types.h>
    ++#else
    ++#include <stdint.h>
    ++#endif
    + 
    + /*
    +  * Version negotiation:
    +@@ -128,42 +127,42 @@
    +    userspace works under 64bit kernels */
    + 
    + struct fuse_attr {
    +-	__u64	ino;
    +-	__u64	size;
    +-	__u64	blocks;
    +-	__u64	atime;
    +-	__u64	mtime;
    +-	__u64	ctime;
    +-	__u32	atimensec;
    +-	__u32	mtimensec;
    +-	__u32	ctimensec;
    +-	__u32	mode;
    +-	__u32	nlink;
    +-	__u32	uid;
    +-	__u32	gid;
    +-	__u32	rdev;
    +-	__u32	blksize;
    +-	__u32	padding;
    ++	uint64_t	ino;
    ++	uint64_t	size;
    ++	uint64_t	blocks;
    ++	uint64_t	atime;
    ++	uint64_t	mtime;
    ++	uint64_t	ctime;
    ++	uint32_t	atimensec;
    ++	uint32_t	mtimensec;
    ++	uint32_t	ctimensec;
    ++	uint32_t	mode;
    ++	uint32_t	nlink;
    ++	uint32_t	uid;
    ++	uint32_t	gid;
    ++	uint32_t	rdev;
    ++	uint32_t	blksize;
    ++	uint32_t	padding;
    + };
    + 
    + struct fuse_kstatfs {
    +-	__u64	blocks;
    +-	__u64	bfree;
    +-	__u64	bavail;
    +-	__u64	files;
    +-	__u64	ffree;
    +-	__u32	bsize;
    +-	__u32	namelen;
    +-	__u32	frsize;
    +-	__u32	padding;
    +-	__u32	spare[6];
    ++	uint64_t	blocks;
    ++	uint64_t	bfree;
    ++	uint64_t	bavail;
    ++	uint64_t	files;
    ++	uint64_t	ffree;
    ++	uint32_t	bsize;
    ++	uint32_t	namelen;
    ++	uint32_t	frsize;
    ++	uint32_t	padding;
    ++	uint32_t	spare[6];
    + };
    + 
    + struct fuse_file_lock {
    +-	__u64	start;
    +-	__u64	end;
    +-	__u32	type;
    +-	__u32	pid; /* tgid */
    ++	uint64_t	start;
    ++	uint64_t	end;
    ++	uint32_t	type;
    ++	uint32_t	pid; /* tgid */
    + };
    + 
    + /**
    +@@ -334,143 +333,143 @@ enum fuse_notify_code {
    + #define FUSE_COMPAT_ENTRY_OUT_SIZE 120
    + 
    + struct fuse_entry_out {
    +-	__u64	nodeid;		/* Inode ID */
    +-	__u64	generation;	/* Inode generation: nodeid:gen must
    ++	uint64_t	nodeid;		/* Inode ID */
    ++	uint64_t	generation;	/* Inode generation: nodeid:gen must
    + 				   be unique for the fs's lifetime */
    +-	__u64	entry_valid;	/* Cache timeout for the name */
    +-	__u64	attr_valid;	/* Cache timeout for the attributes */
    +-	__u32	entry_valid_nsec;
    +-	__u32	attr_valid_nsec;
    ++	uint64_t	entry_valid;	/* Cache timeout for the name */
    ++	uint64_t	attr_valid;	/* Cache timeout for the attributes */
    ++	uint32_t	entry_valid_nsec;
    ++	uint32_t	attr_valid_nsec;
    + 	struct fuse_attr attr;
    + };
    + 
    + struct fuse_forget_in {
    +-	__u64	nlookup;
    ++	uint64_t	nlookup;
    + };
    + 
    + struct fuse_forget_one {
    +-	__u64	nodeid;
    +-	__u64	nlookup;
    ++	uint64_t	nodeid;
    ++	uint64_t	nlookup;
    + };
    + 
    + struct fuse_batch_forget_in {
    +-	__u32	count;
    +-	__u32	dummy;
    ++	uint32_t	count;
    ++	uint32_t	dummy;
    + };
    + 
    + struct fuse_getattr_in {
    +-	__u32	getattr_flags;
    +-	__u32	dummy;
    +-	__u64	fh;
    ++	uint32_t	getattr_flags;
    ++	uint32_t	dummy;
    ++	uint64_t	fh;
    + };
    + 
    + #define FUSE_COMPAT_ATTR_OUT_SIZE 96
    + 
    + struct fuse_attr_out {
    +-	__u64	attr_valid;	/* Cache timeout for the attributes */
    +-	__u32	attr_valid_nsec;
    +-	__u32	dummy;
    ++	uint64_t	attr_valid;	/* Cache timeout for the attributes */
    ++	uint32_t	attr_valid_nsec;
    ++	uint32_t	dummy;
    + 	struct fuse_attr attr;
    + };
    + 
    + #define FUSE_COMPAT_MKNOD_IN_SIZE 8
    + 
    + struct fuse_mknod_in {
    +-	__u32	mode;
    +-	__u32	rdev;
    +-	__u32	umask;
    +-	__u32	padding;
    ++	uint32_t	mode;
    ++	uint32_t	rdev;
    ++	uint32_t	umask;
    ++	uint32_t	padding;
    + };
    + 
    + struct fuse_mkdir_in {
    +-	__u32	mode;
    +-	__u32	umask;
    ++	uint32_t	mode;
    ++	uint32_t	umask;
    + };
    + 
    + struct fuse_rename_in {
    +-	__u64	newdir;
    ++	uint64_t	newdir;
    + };
    + 
    + struct fuse_link_in {
    +-	__u64	oldnodeid;
    ++	uint64_t	oldnodeid;
    + };
    + 
    + struct fuse_setattr_in {
    +-	__u32	valid;
    +-	__u32	padding;
    +-	__u64	fh;
    +-	__u64	size;
    +-	__u64	lock_owner;
    +-	__u64	atime;
    +-	__u64	mtime;
    +-	__u64	unused2;
    +-	__u32	atimensec;
    +-	__u32	mtimensec;
    +-	__u32	unused3;
    +-	__u32	mode;
    +-	__u32	unused4;
    +-	__u32	uid;
    +-	__u32	gid;
    +-	__u32	unused5;
    ++	uint32_t	valid;
    ++	uint32_t	padding;
    ++	uint64_t	fh;
    ++	uint64_t	size;
    ++	uint64_t	lock_owner;
    ++	uint64_t	atime;
    ++	uint64_t	mtime;
    ++	uint64_t	unused2;
    ++	uint32_t	atimensec;
    ++	uint32_t	mtimensec;
    ++	uint32_t	unused3;
    ++	uint32_t	mode;
    ++	uint32_t	unused4;
    ++	uint32_t	uid;
    ++	uint32_t	gid;
    ++	uint32_t	unused5;
    + };
    + 
    + struct fuse_open_in {
    +-	__u32	flags;
    +-	__u32	unused;
    ++	uint32_t	flags;
    ++	uint32_t	unused;
    + };
    + 
    + struct fuse_create_in {
    +-	__u32	flags;
    +-	__u32	mode;
    +-	__u32	umask;
    +-	__u32	padding;
    ++	uint32_t	flags;
    ++	uint32_t	mode;
    ++	uint32_t	umask;
    ++	uint32_t	padding;
    + };
    + 
    + struct fuse_open_out {
    +-	__u64	fh;
    +-	__u32	open_flags;
    +-	__u32	padding;
    ++	uint64_t	fh;
    ++	uint32_t	open_flags;
    ++	uint32_t	padding;
    + };
    + 
    + struct fuse_release_in {
    +-	__u64	fh;
    +-	__u32	flags;
    +-	__u32	release_flags;
    +-	__u64	lock_owner;
    ++	uint64_t	fh;
    ++	uint32_t	flags;
    ++	uint32_t	release_flags;
    ++	uint64_t	lock_owner;
    + };
    + 
    + struct fuse_flush_in {
    +-	__u64	fh;
    +-	__u32	unused;
    +-	__u32	padding;
    +-	__u64	lock_owner;
    ++	uint64_t	fh;
    ++	uint32_t	unused;
    ++	uint32_t	padding;
    ++	uint64_t	lock_owner;
    + };
    + 
    + struct fuse_read_in {
    +-	__u64	fh;
    +-	__u64	offset;
    +-	__u32	size;
    +-	__u32	read_flags;
    +-	__u64	lock_owner;
    +-	__u32	flags;
    +-	__u32	padding;
    ++	uint64_t	fh;
    ++	uint64_t	offset;
    ++	uint32_t	size;
    ++	uint32_t	read_flags;
    ++	uint64_t	lock_owner;
    ++	uint32_t	flags;
    ++	uint32_t	padding;
    + };
    + 
    + #define FUSE_COMPAT_WRITE_IN_SIZE 24
    + 
    + struct fuse_write_in {
    +-	__u64	fh;
    +-	__u64	offset;
    +-	__u32	size;
    +-	__u32	write_flags;
    +-	__u64	lock_owner;
    +-	__u32	flags;
    +-	__u32	padding;
    ++	uint64_t	fh;
    ++	uint64_t	offset;
    ++	uint32_t	size;
    ++	uint32_t	write_flags;
    ++	uint64_t	lock_owner;
    ++	uint32_t	flags;
    ++	uint32_t	padding;
    + };
    + 
    + struct fuse_write_out {
    +-	__u32	size;
    +-	__u32	padding;
    ++	uint32_t	size;
    ++	uint32_t	padding;
    + };
    + 
    + #define FUSE_COMPAT_STATFS_SIZE 48
    +@@ -480,32 +479,32 @@ struct fuse_statfs_out {
    + };
    + 
    + struct fuse_fsync_in {
    +-	__u64	fh;
    +-	__u32	fsync_flags;
    +-	__u32	padding;
    ++	uint64_t	fh;
    ++	uint32_t	fsync_flags;
    ++	uint32_t	padding;
    + };
    + 
    + struct fuse_setxattr_in {
    +-	__u32	size;
    +-	__u32	flags;
    ++	uint32_t	size;
    ++	uint32_t	flags;
    + };
    + 
    + struct fuse_getxattr_in {
    +-	__u32	size;
    +-	__u32	padding;
    ++	uint32_t	size;
    ++	uint32_t	padding;
    + };
    + 
    + struct fuse_getxattr_out {
    +-	__u32	size;
    +-	__u32	padding;
    ++	uint32_t	size;
    ++	uint32_t	padding;
    + };
    + 
    + struct fuse_lk_in {
    +-	__u64	fh;
    +-	__u64	owner;
    ++	uint64_t	fh;
    ++	uint64_t	owner;
    + 	struct fuse_file_lock lk;
    +-	__u32	lk_flags;
    +-	__u32	padding;
    ++	uint32_t	lk_flags;
    ++	uint32_t	padding;
    + };
    + 
    + struct fuse_lk_out {
    +@@ -513,179 +512,179 @@ struct fuse_lk_out {
    + };
    + 
    + struct fuse_access_in {
    +-	__u32	mask;
    +-	__u32	padding;
    ++	uint32_t	mask;
    ++	uint32_t	padding;
    + };
    + 
    + struct fuse_init_in {
    +-	__u32	major;
    +-	__u32	minor;
    +-	__u32	max_readahead;
    +-	__u32	flags;
    ++	uint32_t	major;
    ++	uint32_t	minor;
    ++	uint32_t	max_readahead;
    ++	uint32_t	flags;
    + };
    + 
    + struct fuse_init_out {
    +-	__u32	major;
    +-	__u32	minor;
    +-	__u32	max_readahead;
    +-	__u32	flags;
    +-	__u16   max_background;
    +-	__u16   congestion_threshold;
    +-	__u32	max_write;
    ++	uint32_t	major;
    ++	uint32_t	minor;
    ++	uint32_t	max_readahead;
    ++	uint32_t	flags;
    ++	uint16_t   max_background;
    ++	uint16_t   congestion_threshold;
    ++	uint32_t	max_write;
    + };
    + 
    + #define CUSE_INIT_INFO_MAX 4096
    + 
    + struct cuse_init_in {
    +-	__u32	major;
    +-	__u32	minor;
    +-	__u32	unused;
    +-	__u32	flags;
    ++	uint32_t	major;
    ++	uint32_t	minor;
    ++	uint32_t	unused;
    ++	uint32_t	flags;
    + };
    + 
    + struct cuse_init_out {
    +-	__u32	major;
    +-	__u32	minor;
    +-	__u32	unused;
    +-	__u32	flags;
    +-	__u32	max_read;
    +-	__u32	max_write;
    +-	__u32	dev_major;		/* chardev major */
    +-	__u32	dev_minor;		/* chardev minor */
    +-	__u32	spare[10];
    ++	uint32_t	major;
    ++	uint32_t	minor;
    ++	uint32_t	unused;
    ++	uint32_t	flags;
    ++	uint32_t	max_read;
    ++	uint32_t	max_write;
    ++	uint32_t	dev_major;		/* chardev major */
    ++	uint32_t	dev_minor;		/* chardev minor */
    ++	uint32_t	spare[10];
    + };
    + 
    + struct fuse_interrupt_in {
    +-	__u64	unique;
    ++	uint64_t	unique;
    + };
    + 
    + struct fuse_bmap_in {
    +-	__u64	block;
    +-	__u32	blocksize;
    +-	__u32	padding;
    ++	uint64_t	block;
    ++	uint32_t	blocksize;
    ++	uint32_t	padding;
    + };
    + 
    + struct fuse_bmap_out {
    +-	__u64	block;
    ++	uint64_t	block;
    + };
    + 
    + struct fuse_ioctl_in {
    +-	__u64	fh;
    +-	__u32	flags;
    +-	__u32	cmd;
    +-	__u64	arg;
    +-	__u32	in_size;
    +-	__u32	out_size;
    ++	uint64_t	fh;
    ++	uint32_t	flags;
    ++	uint32_t	cmd;
    ++	uint64_t	arg;
    ++	uint32_t	in_size;
    ++	uint32_t	out_size;
    + };
    + 
    + struct fuse_ioctl_iovec {
    +-	__u64	base;
    +-	__u64	len;
    ++	uint64_t	base;
    ++	uint64_t	len;
    + };
    + 
    + struct fuse_ioctl_out {
    +-	__s32	result;
    +-	__u32	flags;
    +-	__u32	in_iovs;
    +-	__u32	out_iovs;
    ++	int32_t	result;
    ++	uint32_t	flags;
    ++	uint32_t	in_iovs;
    ++	uint32_t	out_iovs;
    + };
    + 
    + struct fuse_poll_in {
    +-	__u64	fh;
    +-	__u64	kh;
    +-	__u32	flags;
    +-	__u32   padding;
    ++	uint64_t	fh;
    ++	uint64_t	kh;
    ++	uint32_t	flags;
    ++	uint32_t   padding;
    + };
    + 
    + struct fuse_poll_out {
    +-	__u32	revents;
    +-	__u32	padding;
    ++	uint32_t	revents;
    ++	uint32_t	padding;
    + };
    + 
    + struct fuse_notify_poll_wakeup_out {
    +-	__u64	kh;
    ++	uint64_t	kh;
    + };
    + 
    + struct fuse_fallocate_in {
    +-	__u64	fh;
    +-	__u64	offset;
    +-	__u64	length;
    +-	__u32	mode;
    +-	__u32	padding;
    ++	uint64_t	fh;
    ++	uint64_t	offset;
    ++	uint64_t	length;
    ++	uint32_t	mode;
    ++	uint32_t	padding;
    + };
    + 
    + struct fuse_in_header {
    +-	__u32	len;
    +-	__u32	opcode;
    +-	__u64	unique;
    +-	__u64	nodeid;
    +-	__u32	uid;
    +-	__u32	gid;
    +-	__u32	pid;
    +-	__u32	padding;
    ++	uint32_t	len;
    ++	uint32_t	opcode;
    ++	uint64_t	unique;
    ++	uint64_t	nodeid;
    ++	uint32_t	uid;
    ++	uint32_t	gid;
    ++	uint32_t	pid;
    ++	uint32_t	padding;
    + };
    + 
    + struct fuse_out_header {
    +-	__u32	len;
    +-	__s32	error;
    +-	__u64	unique;
    ++	uint32_t	len;
    ++	int32_t	error;
    ++	uint64_t	unique;
    + };
    + 
    + struct fuse_dirent {
    +-	__u64	ino;
    +-	__u64	off;
    +-	__u32	namelen;
    +-	__u32	type;
    ++	uint64_t	ino;
    ++	uint64_t	off;
    ++	uint32_t	namelen;
    ++	uint32_t	type;
    + 	char name[];
    + };
    + 
    + #define FUSE_NAME_OFFSET offsetof(struct fuse_dirent, name)
    +-#define FUSE_DIRENT_ALIGN(x) (((x) + sizeof(__u64) - 1) & ~(sizeof(__u64) - 1))
    ++#define FUSE_DIRENT_ALIGN(x) (((x) + sizeof(uint64_t) - 1) & ~(sizeof(uint64_t) - 1))
    + #define FUSE_DIRENT_SIZE(d) \
    + 	FUSE_DIRENT_ALIGN(FUSE_NAME_OFFSET + (d)->namelen)
    + 
    + struct fuse_notify_inval_inode_out {
    +-	__u64	ino;
    +-	__s64	off;
    +-	__s64	len;
    ++	uint64_t	ino;
    ++	int64_t	off;
    ++	int64_t	len;
    + };
    + 
    + struct fuse_notify_inval_entry_out {
    +-	__u64	parent;
    +-	__u32	namelen;
    +-	__u32	padding;
    ++	uint64_t	parent;
    ++	uint32_t	namelen;
    ++	uint32_t	padding;
    + };
    + 
    + struct fuse_notify_delete_out {
    +-	__u64	parent;
    +-	__u64	child;
    +-	__u32	namelen;
    +-	__u32	padding;
    ++	uint64_t	parent;
    ++	uint64_t	child;
    ++	uint32_t	namelen;
    ++	uint32_t	padding;
    + };
    + 
    + struct fuse_notify_store_out {
    +-	__u64	nodeid;
    +-	__u64	offset;
    +-	__u32	size;
    +-	__u32	padding;
    ++	uint64_t	nodeid;
    ++	uint64_t	offset;
    ++	uint32_t	size;
    ++	uint32_t	padding;
    + };
    + 
    + struct fuse_notify_retrieve_out {
    +-	__u64	notify_unique;
    +-	__u64	nodeid;
    +-	__u64	offset;
    +-	__u32	size;
    +-	__u32	padding;
    ++	uint64_t	notify_unique;
    ++	uint64_t	nodeid;
    ++	uint64_t	offset;
    ++	uint32_t	size;
    ++	uint32_t	padding;
    + };
    + 
    + /* Matches the size of fuse_write_in */
    + struct fuse_notify_retrieve_in {
    +-	__u64	dummy1;
    +-	__u64	offset;
    +-	__u32	size;
    +-	__u32	dummy2;
    +-	__u64	dummy3;
    +-	__u64	dummy4;
    ++	uint64_t	dummy1;
    ++	uint64_t	offset;
    ++	uint32_t	size;
    ++	uint32_t	dummy2;
    ++	uint64_t	dummy3;
    ++	uint64_t	dummy4;
    + };
    + 
    + #endif /* _LINUX_FUSE_H */
    diff --git c/var/spack/repos/builtin/packages/libfuse/package.py i/var/spack/repos/builtin/packages/libfuse/package.py
    index 57d62e0bf6..5bc57f0b86 100644
    --- c/var/spack/repos/builtin/packages/libfuse/package.py
    +++ i/var/spack/repos/builtin/packages/libfuse/package.py
    @@ -94,6 +94,13 @@ def url_for_version(self, version):
             sha256="94d5c6d9785471147506851b023cb111ef2081d1c0e695728037bbf4f64ce30a",
             when="@:2",
         )
    +    # fixed in v3.x, but some packages still require v2.x
    +    # backport of https://github.com/libfuse/libfuse/commit/6b02a7082ae4c560427ff95b51aa8930bb4a6e1f
    +    patch(
    +        "fix_aarch64_compile.patch",
    +        sha256="6ced88c987543d8e62614fa9bd796e7ede7238d55cc50910ece4355c9c4e57d6",
    +        when="@:2 target=aarch64:",
    +    )
     
         executables = ["^fusermount3?$"]
     
    diff --git c/var/spack/repos/builtin/packages/nccl/package.py i/var/spack/repos/builtin/packages/nccl/package.py
    index d70ee8180d..cc8ff49958 100644
    --- c/var/spack/repos/builtin/packages/nccl/package.py
    +++ i/var/spack/repos/builtin/packages/nccl/package.py
    @@ -12,11 +12,12 @@ class Nccl(MakefilePackage, CudaPackage):
         """Optimized primitives for collective multi-GPU communication."""
     
         homepage = "https://github.com/NVIDIA/nccl"
    -    url = "https://github.com/NVIDIA/nccl/archive/v2.7.3-1.tar.gz"
    +    url = "https://github.com/NVIDIA/nccl/archive/v2.26.2-1.tar.gz"
     
         maintainers("adamjstewart")
         libraries = ["libnccl.so"]
     
    +    version("2.26.2-1", sha256="74c6ab40c864d79c2139508e9419de5970cb406ec85f001d5f834d5f5c0c4f3b")
         version("2.22.3-1", sha256="45151629a9494460e73375281e8b0fe379141528879301899ece9b776faca024")
         version("2.21.5-1", sha256="1923596984d85e310b5b6c52b2c72a1b93da57218f2bc5a5c7ac3d59297a3303")
         version("2.20.3-1", sha256="19456bd63ca7d23a8319cbbdbaaf6c25949dd51161a9f8809f6b7453282983dd")
    diff --git c/var/spack/repos/builtin/packages/nvtx/package.py i/var/spack/repos/builtin/packages/nvtx/package.py
    index c6f6af4381..10bb5321cc 100644
    --- c/var/spack/repos/builtin/packages/nvtx/package.py
    +++ i/var/spack/repos/builtin/packages/nvtx/package.py
    @@ -4,6 +4,7 @@
     # SPDX-License-Identifier: (Apache-2.0 OR MIT)
     
     from spack.package import *
    +from spack import build_systems
     
     
     class Nvtx(Package, PythonExtension):
    @@ -49,4 +50,4 @@ def install(self, spec, prefix):
             install("./nvtx-config.cmake", prefix)  # added by the patch above
     
             with working_dir(self.build_directory):
    -            pip(*PythonPipBuilder.std_args(self), f"--prefix={self.prefix}", ".")
    +            pip(*build_systems.python.PythonPipBuilder.std_args(self), f"--prefix={self.prefix}", ".")
    diff --git c/var/spack/repos/builtin/packages/py-cython/package.py i/var/spack/repos/builtin/packages/py-cython/package.py
    index 96d60cb768..8f1bb659d4 100644
    --- c/var/spack/repos/builtin/packages/py-cython/package.py
    +++ i/var/spack/repos/builtin/packages/py-cython/package.py
    @@ -1,5 +1,4 @@
    -# Copyright 2013-2024 Lawrence Livermore National Security, LLC and other
    -# Spack Project Developers. See the top-level COPYRIGHT file for details.
    +# Copyright Spack Project Developers. See COPYRIGHT file for details.
     #
     # SPDX-License-Identifier: (Apache-2.0 OR MIT)
     
    @@ -10,16 +9,12 @@ class PyCython(PythonPackage):
         """The Cython compiler for writing C extensions for the Python language."""
     
         homepage = "https://github.com/cython/cython"
    -    pypi = "cython/Cython-0.29.21.tar.gz"
    +    pypi = "cython/cython-3.0.11.tar.gz"
         tags = ["build-tools"]
     
         license("Apache-2.0")
     
    -    version(
    -        "3.0.11",
    -        sha256="7146dd2af8682b4ca61331851e6aebce9fe5158e75300343f80c07ca80b1faff",
    -        url="https://files.pythonhosted.org/packages/source/cython/cython-3.0.11.tar.gz",
    -    )
    +    version("3.0.11", sha256="7146dd2af8682b4ca61331851e6aebce9fe5158e75300343f80c07ca80b1faff")
         version("3.0.10", sha256="dcc96739331fb854dcf503f94607576cfe8488066c61ca50dfd55836f132de99")
         version("3.0.8", sha256="8333423d8fd5765e7cceea3a9985dd1e0a5dfeb2734629e1a2ed2d6233d39de6")
         version("3.0.7", sha256="fb299acf3a578573c190c858d49e0cf9d75f4bc49c3f24c5a63804997ef09213")
    @@ -37,42 +32,83 @@ class PyCython(PythonPackage):
         version("0.29.23", sha256="6a0d31452f0245daacb14c979c77e093eb1a546c760816b5eed0047686baad8e")
         version("0.29.22", sha256="df6b83c7a6d1d967ea89a2903e4a931377634a297459652e4551734c48195406")
         version("0.29.21", sha256="e57acb89bd55943c8d8bf813763d20b9099cc7165c0f16b707631a7654be9cad")
    -    version("0.29.20", sha256="22d91af5fc2253f717a1b80b8bb45acb655f643611983fd6f782b9423f8171c7")
    -    version("0.29.16", sha256="232755284f942cbb3b43a06cd85974ef3c970a021aef19b5243c03ee2b08fa05")
    -    version("0.29.15", sha256="60d859e1efa5cc80436d58aecd3718ff2e74b987db0518376046adedba97ac30")
    -    version("0.29.14", sha256="e4d6bb8703d0319eb04b7319b12ea41580df44fd84d83ccda13ea463c6801414")
    -    version("0.29.13", sha256="c29d069a4a30f472482343c866f7486731ad638ef9af92bfe5fca9c7323d638e")
    -    version("0.29.10", sha256="26229570d6787ff3caa932fe9d802960f51a89239b990d275ae845405ce43857")
    -    version("0.29.7", sha256="55d081162191b7c11c7bfcb7c68e913827dfd5de6ecdbab1b99dab190586c1e8")
    -    version("0.29.5", sha256="9d5290d749099a8e446422adfb0aa2142c711284800fb1eb70f595101e32cbf1")
    -    version("0.29", sha256="94916d1ede67682638d3cc0feb10648ff14dc51fb7a7f147f4fedce78eaaea97")
    -    version("0.28.6", sha256="68aa3c00ef1deccf4dd50f0201d47c268462978c12c42943bc33dc9dc816ac1b")
    -    version("0.28.3", sha256="1aae6d6e9858888144cea147eb5e677830f45faaff3d305d77378c3cba55f526")
    -    version("0.28.1", sha256="152ee5f345012ca3bb7cc71da2d3736ee20f52cd8476e4d49e5e25c5a4102b12")
    -    version("0.25.2", sha256="f141d1f9c27a07b5a93f7dc5339472067e2d7140d1c5a9e20112a5665ca60306")
    -    version("0.23.5", sha256="0ae5a5451a190e03ee36922c4189ca2c88d1df40a89b4f224bc842d388a0d1b6")
    -    version("0.23.4", sha256="fec42fecee35d6cc02887f1eef4e4952c97402ed2800bfe41bbd9ed1a0730d8e")
    -
    -    depends_on("c", type="build")  # generated
    -    depends_on("cxx", type="build")  # generated
    -
    -    # https://github.com/cython/cython/issues/5751 (distutils not yet dropped)
    -    depends_on("python@:3.11", type=("build", "link", "run"))
    -
    -    # https://github.com/cython/cython/commit/1cd24026e9cf6d63d539b359f8ba5155fd48ae21
    -    # collections.Iterable was removed in Python 3.10
    -    depends_on("python@:3.9", when="@:0.29.14", type=("build", "link", "run"))
    -
    -    # https://github.com/cython/cython/commit/430e2ca220c8fed49604daf578df98aadb33a87d
    -    depends_on("python@:3.8", when="@:0.29.13", type=("build", "link", "run"))
    -
    -    depends_on("py-setuptools", type=("build", "run"))
    +    with default_args(deprecated=True):
    +        version(
    +            "0.29.20", sha256="22d91af5fc2253f717a1b80b8bb45acb655f643611983fd6f782b9423f8171c7"
    +        )
    +        version(
    +            "0.29.16", sha256="232755284f942cbb3b43a06cd85974ef3c970a021aef19b5243c03ee2b08fa05"
    +        )
    +        version(
    +            "0.29.15", sha256="60d859e1efa5cc80436d58aecd3718ff2e74b987db0518376046adedba97ac30"
    +        )
    +        version(
    +            "0.29.14", sha256="e4d6bb8703d0319eb04b7319b12ea41580df44fd84d83ccda13ea463c6801414"
    +        )
    +        version(
    +            "0.29.13", sha256="c29d069a4a30f472482343c866f7486731ad638ef9af92bfe5fca9c7323d638e"
    +        )
    +        version(
    +            "0.29.10", sha256="26229570d6787ff3caa932fe9d802960f51a89239b990d275ae845405ce43857"
    +        )
    +        version(
    +            "0.29.7", sha256="55d081162191b7c11c7bfcb7c68e913827dfd5de6ecdbab1b99dab190586c1e8"
    +        )
    +        version(
    +            "0.29.5", sha256="9d5290d749099a8e446422adfb0aa2142c711284800fb1eb70f595101e32cbf1"
    +        )
    +        version("0.29", sha256="94916d1ede67682638d3cc0feb10648ff14dc51fb7a7f147f4fedce78eaaea97")
    +        version(
    +            "0.28.6", sha256="68aa3c00ef1deccf4dd50f0201d47c268462978c12c42943bc33dc9dc816ac1b"
    +        )
    +        version(
    +            "0.28.3", sha256="1aae6d6e9858888144cea147eb5e677830f45faaff3d305d77378c3cba55f526"
    +        )
    +        version(
    +            "0.28.1", sha256="152ee5f345012ca3bb7cc71da2d3736ee20f52cd8476e4d49e5e25c5a4102b12"
    +        )
    +        version(
    +            "0.25.2", sha256="f141d1f9c27a07b5a93f7dc5339472067e2d7140d1c5a9e20112a5665ca60306"
    +        )
    +        version(
    +            "0.23.5", sha256="0ae5a5451a190e03ee36922c4189ca2c88d1df40a89b4f224bc842d388a0d1b6"
    +        )
    +        version(
    +            "0.23.4", sha256="fec42fecee35d6cc02887f1eef4e4952c97402ed2800bfe41bbd9ed1a0730d8e"
    +        )
    +
    +    depends_on("c", type="build")
    +    depends_on("cxx", type="build")
    +
    +    # Based on PyPI wheel availability
    +    with default_args(type=("build", "link", "run")):
    +        depends_on("python@:3.13")
    +        depends_on("python@:3.12", when="@:3.0.10")
    +        depends_on("python@:3.11", when="@:3.0.3")  # Cythonize still used distutils
    +        depends_on("python@:3.10", when="@:0.29.28")
    +        depends_on("python@:3.9", when="@:0.29.24")
    +        depends_on("python@:3.8", when="@:0.29.20")
    +        depends_on("python@:3.7", when="@:0.29.13")
    +
    +    # https://github.com/cython/cython/issues/5751
    +    # https://github.com/cython/cython/commit/0000fb4c319ef8f7e8eabcc99677f99a8c503cc3
    +    depends_on("py-setuptools@66:", when="^python@3.12:", type="run")
    +
    +    depends_on("py-setuptools", type="build")
         depends_on("gdb@7.2:", type="test")
     
         # Backports CYTHON_FORCE_REGEN environment variable
         patch("5307.patch", when="@0.29:0.29.33")
         patch("5712.patch", when="@0.29")
     
    +    def url_for_version(self, version):
    +        url = "https://files.pythonhosted.org/packages/source/c/cython/{}-{}.tar.gz"
    +        if version >= Version("3.0.11"):
    +            name = "cython"
    +        else:
    +            name = "Cython"
    +        return url.format(name, version)
    +
         @property
         def command(self):
             """Returns the Cython command"""
    diff --git c/var/spack/repos/builtin/packages/py-dockerpy-creds/package.py i/var/spack/repos/builtin/packages/py-dockerpy-creds/package.py
    index ed1788feea..0253c031f8 100644
    --- c/var/spack/repos/builtin/packages/py-dockerpy-creds/package.py
    +++ i/var/spack/repos/builtin/packages/py-dockerpy-creds/package.py
    @@ -25,3 +25,9 @@ class PyDockerpyCreds(PythonPackage):
         depends_on("python@2.0:2.8,3.4:", type=("build", "run"))
         depends_on("py-setuptools", type="build")
         depends_on("py-six", type=("build", "run"))
    +
    +    patch(
    +        "https://patch-diff.githubusercontent.com/raw/shin-/dockerpy-creds/pull/15.patch?full_index=1",
    +        sha256="e1a9f6312636db956a8c2136c5c5ab99d7351ae91de9bdbd4fe7718cf3665561",
    +        when="@0.4.0",
    +    )
    diff --git c/var/spack/repos/builtin/packages/py-donfig/package.py i/var/spack/repos/builtin/packages/py-donfig/package.py
    new file mode 100644
    index 0000000000..e34fd58855
    --- /dev/null
    +++ i/var/spack/repos/builtin/packages/py-donfig/package.py
    @@ -0,0 +1,24 @@
    +# Copyright Spack Project Developers. See COPYRIGHT file for details.
    +#
    +# SPDX-License-Identifier: (Apache-2.0 OR MIT)
    +
    +from spack.package import *
    +
    +
    +class PyDonfig(PythonPackage):
    +    """Donfig is a python library making package and script configuration easy"""
    +
    +    homepage = "https://donfig.readthedocs.io/en/latest/"
    +    pypi = "donfig/donfig-0.8.1.post1.tar.gz"
    +
    +    maintainers("Chrismarsh")
    +
    +    license("MIT", checked_by="Chrismarsh")
    +
    +    version(
    +        "0.8.1.post1", sha256="3bef3413a4c1c601b585e8d297256d0c1470ea012afa6e8461dc28bfb7c23f52"
    +    )
    +
    +    depends_on("py-setuptools@62.6:", type="build")
    +    depends_on("py-versioneer@0.28: +toml")
    +    depends_on("py-pyyaml", type=("build", "run"))
    diff --git c/var/spack/repos/builtin/packages/py-hf-transfer/package.py i/var/spack/repos/builtin/packages/py-hf-transfer/package.py
    new file mode 100644
    index 0000000000..1b7b2bd778
    --- /dev/null
    +++ i/var/spack/repos/builtin/packages/py-hf-transfer/package.py
    @@ -0,0 +1,20 @@
    +# Copyright 2013-2024 Lawrence Livermore National Security, LLC and other
    +# Spack Project Developers. See the top-level COPYRIGHT file for details.
    +#
    +# SPDX-License-Identifier: (Apache-2.0 OR MIT)
    +
    +from spack.package import *
    +
    +
    +class PyHfTransfer(PythonPackage):
    +    """Speed up file transfers with the Hugging Face Hub."""
    +
    +    homepage = "https://github.com/huggingface/hf_transfer"
    +    pypi = "hf_transfer/hf_transfer-0.1.8.tar.gz"
    +
    +    license("Apache-2.0")
    +
    +    version("0.1.8", sha256="26d229468152e7a3ec12664cac86b8c2800695fd85f9c9a96677a775cc04f0b3")
    +
    +    with default_args(type="build"):
    +        depends_on("py-maturin@1.4:")
    diff --git c/var/spack/repos/builtin/packages/py-huggingface-hub/package.py i/var/spack/repos/builtin/packages/py-huggingface-hub/package.py
    index 2de20bed53..b20bca5396 100644
    --- c/var/spack/repos/builtin/packages/py-huggingface-hub/package.py
    +++ i/var/spack/repos/builtin/packages/py-huggingface-hub/package.py
    @@ -16,6 +16,7 @@ class PyHuggingfaceHub(PythonPackage):
     
         license("Apache-2.0")
     
    +    version("0.26.2", sha256="b100d853465d965733964d123939ba287da60a547087783ddff8a323f340332b")
         version("0.24.6", sha256="cc2579e761d070713eaa9c323e3debe39d5b464ae3a7261c39a9195b27bb8000")
         version("0.23.4", sha256="35d99016433900e44ae7efe1c209164a5a81dbbcd53a52f99c281dcd7ce22431")
         version("0.19.4", sha256="176a4fc355a851c17550e7619488f383189727eab209534d7cef2114dae77b22")
    @@ -30,17 +31,34 @@ class PyHuggingfaceHub(PythonPackage):
             when="@0.10:",
             description="Install dependencies for CLI-specific features",
         )
    +    variant(
    +        "hf_transfer",
    +        default=False,
    +        when="@0.21:",
    +        description="Install hf_transfer to speed up downloads/uploads",
    +    )
    +
    +    with default_args(type="build"):
    +        depends_on("py-setuptools")
    +
    +    with default_args(type=("build", "run")):
    +        depends_on("py-filelock")
    +        depends_on("py-fsspec@2023.5:", when="@0.18:")
    +        depends_on("py-fsspec", when="@0.14:")
    +        depends_on("py-packaging@20.9:", when="@0.10:")
    +        depends_on("py-pyyaml@5.1:", when="@0.10:")
    +        depends_on("py-requests")
    +        depends_on("py-tqdm@4.42.1:", when="@0.12:")
    +        depends_on("py-tqdm")
    +        depends_on("py-typing-extensions@3.7.4.3:", when="@0.10:")
    +        depends_on("py-typing-extensions", when="@0.0.10:")
    +
    +        with when("+cli"):
    +            depends_on("py-inquirerpy@0.3.4")
    +
    +        with when("+hf_transfer"):
    +            depends_on("py-hf-transfer@0.1.4:")
     
    -    depends_on("py-setuptools", type="build")
    -    depends_on("py-filelock", type=("build", "run"))
    -    depends_on("py-fsspec@2023.5:", when="@0.18:", type=("build", "run"))
    -    depends_on("py-fsspec", when="@0.14:", type=("build", "run"))
    -    depends_on("py-packaging@20.9:", when="@0.10:", type=("build", "run"))
    -    depends_on("py-pyyaml@5.1:", when="@0.10:", type=("build", "run"))
    -    depends_on("py-requests", type=("build", "run"))
    -    depends_on("py-tqdm@4.42.1:", when="@0.12:", type=("build", "run"))
    -    depends_on("py-tqdm", type=("build", "run"))
    -    depends_on("py-typing-extensions@3.7.4.3:", when="@0.10:", type=("build", "run"))
    -    depends_on("py-typing-extensions", when="@0.0.10:", type=("build", "run"))
    -
    -    depends_on("py-inquirerpy@0.3.4", when="@0.14:+cli", type=("build", "run"))
    +    def setup_run_environment(self, env):
    +        if "+hf_transfer" in self.spec:
    +            env.set("HF_HUB_ENABLE_HF_TRANSFER", 1)
    diff --git c/var/spack/repos/builtin/packages/py-numcodecs/package.py i/var/spack/repos/builtin/packages/py-numcodecs/package.py
    index 15da017a92..2261a8fce5 100644
    --- c/var/spack/repos/builtin/packages/py-numcodecs/package.py
    +++ i/var/spack/repos/builtin/packages/py-numcodecs/package.py
    @@ -24,6 +24,11 @@ class PyNumcodecs(PythonPackage):
     
         version("main", branch="main", submodules=True)
         version("master", branch="main", submodules=True, deprecated=True)
    +    version(
    +        "0.15.0",
    +        sha256="52fb0c20d99845ef600eb3f8c8ad3e22fe2cb4f2a53394d331210af7cc3375ca",
    +        preferred=True,
    +    )
         version("0.13.0", sha256="ba4fac7036ea5a078c7afe1d4dffeb9685080d42f19c9c16b12dad866703aa2e")
         version("0.12.1", sha256="05d91a433733e7eef268d7e80ec226a0232da244289614a8f3826901aec1098e")
         version("0.12.0", sha256="6388e5f4e94d18a7165fbd1c9d3637673b74157cff8bc644005f9e2a4c717d6e")
    @@ -50,7 +55,7 @@ class PyNumcodecs(PythonPackage):
         depends_on("py-entrypoints", when="@0.10.1:0.11", type=("build", "run"))
         depends_on("py-msgpack", type=("build", "run"), when="+msgpack")
     
    -    patch("apple-clang-12.patch", when="%apple-clang@12:")
    +    patch("apple-clang-12.patch", when="%apple-clang@12: @:0.13")
     
         # TODO: this package should really depend on blosc, zstd, lz4, zlib, but right now it vendors
         # those libraries without any way to use the system versions.
    diff --git c/var/spack/repos/builtin/packages/py-pybind11/package.py i/var/spack/repos/builtin/packages/py-pybind11/package.py
    index b14b50a8e6..0ace79bba6 100644
    --- c/var/spack/repos/builtin/packages/py-pybind11/package.py
    +++ i/var/spack/repos/builtin/packages/py-pybind11/package.py
    @@ -27,6 +27,7 @@ class PyPybind11(CMakePackage, PythonExtension):
         maintainers("ax3l")
     
         version("master", branch="master")
    +    version("2.13.6", sha256="e08cb87f4773da97fa7b5f035de8763abc656d87d5773e62f6da0587d1f0ec20")
         version("2.13.5", sha256="b1e209c42b3a9ed74da3e0b25a4f4cd478d89d5efbb48f04b277df427faf6252")
         version("2.13.4", sha256="efc901aa0aab439a3fea6efeaf930b5a349fb06394bf845c64ce15a9cf8f0240")
         version("2.13.3", sha256="6e7a84ec241544f2f5e30c7a82c09c81f0541dd14e9d9ef61051e07105f9c445")
    diff --git c/var/spack/repos/builtin/packages/py-pydantic-core/package.py i/var/spack/repos/builtin/packages/py-pydantic-core/package.py
    index ec7dd02dfa..5bc50895c9 100644
    --- c/var/spack/repos/builtin/packages/py-pydantic-core/package.py
    +++ i/var/spack/repos/builtin/packages/py-pydantic-core/package.py
    @@ -15,8 +15,12 @@ class PyPydanticCore(PythonPackage):
     
         license("MIT", checked_by="qwertos")
     
    +    version("2.27.1", sha256="62a763352879b84aa31058fc931884055fd75089cccbd9d58bb6afd01141b235")
         version("2.18.4", sha256="ec3beeada09ff865c344ff3bc2f427f5e6c26401cc6113d77e372c3fdac73864")
     
    +    # Based on PyPI wheel availability
    +    depends_on("python@:3.13", type=("build", "run"))
    +    depends_on("python@:3.12", when="@:2.19", type=("build", "run"))
         depends_on("rust@1.76:", type="build")
         depends_on("py-maturin@1", type="build")
         depends_on("py-typing-extensions@4.6,4.7.1:", type="build")
    diff --git c/var/spack/repos/builtin/packages/py-pydantic/package.py i/var/spack/repos/builtin/packages/py-pydantic/package.py
    index bfc6aa639b..8de4cf2e53 100644
    --- c/var/spack/repos/builtin/packages/py-pydantic/package.py
    +++ i/var/spack/repos/builtin/packages/py-pydantic/package.py
    @@ -14,6 +14,7 @@ class PyPydantic(PythonPackage):
     
         license("MIT")
     
    +    version("2.10.1", sha256="a4daca2dc0aa429555e0656d6bf94873a7dc5f54ee42b1f5873d666fb3f35560")
         version("2.7.4", sha256="0c84efd9548d545f63ac0060c1e4d39bb9b14db8b3c0652338aecc07b5adec52")
         version("1.10.9", sha256="95c70da2cd3b6ddf3b9645ecaa8d98f3d80c606624b6d245558d202cd23ea3be")
         version("1.10.2", sha256="91b8e218852ef6007c2b98cd861601c6a09f1aa32bbbb74fab5b1c33d4a1e410")
    @@ -25,12 +26,15 @@ class PyPydantic(PythonPackage):
         depends_on("py-setuptools", type="build", when="@1")
         depends_on("py-hatchling", type="build", when="@2")
         depends_on("py-hatch-fancy-pypi-readme@22.5.0:", type="build", when="@2")
    +    depends_on("py-typing-extensions@4.12.2:", when="@2.10:", type=("build", "run"))
         depends_on("py-typing-extensions@4.6.1:", when="@2.7.1:", type=("build", "run"))
         depends_on("py-typing-extensions@4.2:", when="@1.10.9:", type=("build", "run"))
         depends_on("py-typing-extensions@4.1:", when="@1.10:", type=("build", "run"))
         depends_on("py-typing-extensions@3.7.4.3:", type=("build", "run"))
     
    +    depends_on("py-annotated-types@0.6:", type=("build", "run"), when="@2.10:")
         depends_on("py-annotated-types@0.4.0:", type=("build", "run"), when="@2.7.4:")
    +    depends_on("py-pydantic-core@2.27.1", type=("build", "run"), when="@2.10.1")
         depends_on("py-pydantic-core@2.18.4", type=("build", "run"), when="@2.7.4")
     
         depends_on("py-python-dotenv@0.10.4:", when="@1 +dotenv", type=("build", "run"))
    diff --git c/var/spack/repos/builtin/packages/py-safetensors/package.py i/var/spack/repos/builtin/packages/py-safetensors/package.py
    index f0f11247c5..741a8d8ba4 100644
    --- c/var/spack/repos/builtin/packages/py-safetensors/package.py
    +++ i/var/spack/repos/builtin/packages/py-safetensors/package.py
    @@ -12,9 +12,12 @@ class PySafetensors(PythonPackage):
         homepage = "https://github.com/huggingface/safetensors"
         pypi = "safetensors/safetensors-0.3.1.tar.gz"
     
    +    version("0.4.5", sha256="d73de19682deabb02524b3d5d1f8b3aaba94c72f1bbfc7911b9b9d5d391c0310")
         version("0.4.3", sha256="2f85fc50c4e07a21e95c24e07460fe6f7e2859d0ce88092838352b798ce711c2")
         version("0.3.1", sha256="571da56ff8d0bec8ae54923b621cda98d36dcef10feb36fd492c4d0c2cd0e869")
     
    -    depends_on("py-setuptools", type="build")
    -    depends_on("py-setuptools-rust", type="build")
    -    depends_on("py-maturin", type="build", when="@0.4.3")
    +    # Based on PyPI wheel availability
    +    depends_on("python@:3.12", when="@:0.4.3", type=("build", "run"))
    +    depends_on("py-maturin@1", type="build", when="@0.4.3:")
    +    depends_on("py-setuptools", when="@0.3.1", type="build")
    +    depends_on("py-setuptools-rust", when="@0.3.1", type="build")
    diff --git c/var/spack/repos/builtin/packages/py-sentencepiece/package.py i/var/spack/repos/builtin/packages/py-sentencepiece/package.py
    index 2a1fdff88f..186e6f5dfd 100644
    --- c/var/spack/repos/builtin/packages/py-sentencepiece/package.py
    +++ i/var/spack/repos/builtin/packages/py-sentencepiece/package.py
    @@ -19,6 +19,7 @@ class PySentencepiece(PythonPackage):
     
         license("Apache-2.0")
     
    +    version("0.1.99", sha256="63617eaf56c7a3857597dcd8780461f57dd21381b56a27716ef7d7e02e14ced4")
         version("0.1.91", sha256="acbc7ea12713cd2a8d64892f8d2033c7fd2bb4faecab39452496120ace9a4b1b")
         version("0.1.85", sha256="dd4956287a1b6af3cbdbbd499b7227a859a4e3f41c9882de5e6bdd929e219ae6")
     
    @@ -27,6 +28,7 @@ class PySentencepiece(PythonPackage):
         depends_on("sentencepiece")
         depends_on("sentencepiece@0.1.85", when="@0.1.85")
         depends_on("sentencepiece@0.1.91", when="@0.1.91")
    +    depends_on("sentencepiece@0.1.99", when="@0.1.99")
         depends_on("pkgconfig", type="build")
         depends_on("py-setuptools", type="build")
     
    diff --git c/var/spack/repos/builtin/packages/py-sentry-sdk/package.py i/var/spack/repos/builtin/packages/py-sentry-sdk/package.py
    index 3a25cfd103..bc9b4c365f 100644
    --- c/var/spack/repos/builtin/packages/py-sentry-sdk/package.py
    +++ i/var/spack/repos/builtin/packages/py-sentry-sdk/package.py
    @@ -10,10 +10,11 @@ class PySentrySdk(PythonPackage):
         """The new Python SDK for Sentry.io"""
     
         homepage = "https://github.com/getsentry/sentry-python"
    -    pypi = "sentry-sdk/sentry-sdk-0.17.6.tar.gz"
    +    pypi = "sentry-sdk/sentry_sdk-2.0.0.tar.gz"
     
         license("MIT")
     
    +    version("2.22.0", sha256="b4bf43bb38f547c84b2eadcefbe389b36ef75f3f38253d7a74d6b928c07ae944")
         version("1.5.5", sha256="98fd155fa5d5fec1dbabed32a1a4ae2705f1edaa5dae4e7f7b62a384ba30e759")
         version("0.17.6", sha256="1a086486ff9da15791f294f6e9915eb3747d161ef64dee2d038a4d0b4a369b24")
     
    @@ -36,6 +37,7 @@ class PySentrySdk(PythonPackage):
     
         depends_on("python@2.7,3.4:", type=("build", "run"))
         depends_on("py-setuptools", type="build")
    +    depends_on("py-urllib3@1.26.11:", when="@2.22:", type=("build", "run"))
         depends_on("py-urllib3@1.10.0:", type=("build", "run"))
         depends_on("py-certifi", type=("build", "run"))
     
    diff --git c/var/spack/repos/builtin/packages/py-setuptools-scm/package.py i/var/spack/repos/builtin/packages/py-setuptools-scm/package.py
    index f1ee81b5e9..b66d329957 100644
    --- c/var/spack/repos/builtin/packages/py-setuptools-scm/package.py
    +++ i/var/spack/repos/builtin/packages/py-setuptools-scm/package.py
    @@ -15,6 +15,7 @@ class PySetuptoolsScm(PythonPackage):
     
         license("MIT")
     
    +    version("8.1.0", sha256="42dea1b65771cba93b7a515d65a65d8246e560768a66b9106a592c8e7f26c8a7")
         version("8.0.4", sha256="b5f43ff6800669595193fd09891564ee9d1d7dcb196cab4b2506d53a2e1c95c7")
         version("7.1.0", sha256="6c508345a771aad7d56ebff0e70628bf2b0ec7573762be9960214730de278f27")
         version("7.0.5", sha256="031e13af771d6f892b941adb6ea04545bbf91ebc5ce68c78aaf3fff6e1fb4844")
    diff --git c/var/spack/repos/builtin/packages/py-sympy/package.py i/var/spack/repos/builtin/packages/py-sympy/package.py
    index 9145b60411..ea470f8262 100644
    --- c/var/spack/repos/builtin/packages/py-sympy/package.py
    +++ i/var/spack/repos/builtin/packages/py-sympy/package.py
    @@ -13,6 +13,7 @@ class PySympy(PythonPackage):
     
         license("BSD-3-Clause")
     
    +    version("1.13.1", sha256="9cebf7e04ff162015ce31c9c6c9144daa34a93bd082f54fd8f12deca4f47515f")
         version("1.13.0", sha256="3b6af8f4d008b9a1a6a4268b335b984b23835f26d1d60b0526ebc71d48a25f57")
         version("1.12", sha256="ebf595c8dac3e0fdc4152c51878b498396ec7f30e7a914d6071e674d49420fb8")
         version("1.11.1", sha256="e32380dce63cb7c0108ed525570092fd45168bdae2faa17e528221ef72e88658")
    diff --git c/var/spack/repos/builtin/packages/py-tokenizers/package.py i/var/spack/repos/builtin/packages/py-tokenizers/package.py
    index 4ff2c87d31..6e223068de 100644
    --- c/var/spack/repos/builtin/packages/py-tokenizers/package.py
    +++ i/var/spack/repos/builtin/packages/py-tokenizers/package.py
    @@ -13,6 +13,7 @@ class PyTokenizers(PythonPackage):
         homepage = "https://github.com/huggingface/tokenizers"
         pypi = "tokenizers/tokenizers-0.6.0.tar.gz"
     
    +    version("0.21.0", sha256="ee0894bf311b75b0c03079f33859ae4b2334d675d4e93f5a4132e1eae2834fe4")
         version("0.19.1", sha256="ee59e6680ed0fdbe6b724cf38bd70400a0c1dd623b07ac729087270caeac88e3")
         version("0.15.0", sha256="10c7e6e7b4cabd757da59e93f5f8d1126291d16f8b54f28510825ef56a3e5d0e")
         version("0.13.3", sha256="2e546dbb68b623008a5442353137fbb0123d311a6d7ba52f2667c8862a75af2e")
    @@ -30,8 +31,8 @@ class PyTokenizers(PythonPackage):
         )
     
         # TODO: This package currently requires internet access to install.
    -    depends_on("py-maturin@1", when="@0.14:", type="build")
    -    depends_on("py-huggingface-hub@0.16.4:0", when="@0.15:", type=("build", "run"))
    +    depends_on("py-maturin@1:", when="@0.14:", type="build")
    +    depends_on("py-huggingface-hub@0.16.4:", when="@0.15:", type=("build", "run"))
     
         # cargo resolves dependencies, which includes openssl-sys somewhere, which needs
         # system pkgconfig and openssl.
    diff --git c/var/spack/repos/builtin/packages/py-torch-nvidia-apex/package.py i/var/spack/repos/builtin/packages/py-torch-nvidia-apex/package.py
    index a0ca87cd8b..e3e611daa6 100644
    --- c/var/spack/repos/builtin/packages/py-torch-nvidia-apex/package.py
    +++ i/var/spack/repos/builtin/packages/py-torch-nvidia-apex/package.py
    @@ -1,5 +1,4 @@
    -# Copyright 2013-2024 Lawrence Livermore National Security, LLC and other
    -# Spack Project Developers. See the top-level COPYRIGHT file for details.
    +# Copyright Spack Project Developers. See COPYRIGHT file for details.
     #
     # SPDX-License-Identifier: (Apache-2.0 OR MIT)
     
    @@ -18,63 +17,94 @@ class PyTorchNvidiaApex(PythonPackage, CudaPackage):
         license("BSD-3-Clause")
     
         version("master", branch="master")
    -    version("24.04.01", sha256="065bc5c0146ee579d5db2b38ca3949da4dc799b871961a2c9eb19e18892166ce")
    +    version("25.02.14", commit="b216eeee7dd91478745496919e9c0167cc4c41e3", submodules=True)
    +    version(
    +        "24.04.01",
    +        sha256="065bc5c0146ee579d5db2b38ca3949da4dc799b871961a2c9eb19e18892166ce",
    +        preferred=True,
    +    )
         version("23.08", tag="23.08")
         version("23.07", tag="23.07")
         version("23.06", tag="23.06")
         version("23.05", tag="23.05")
         version("22.03", tag="22.03")
    -    version("2020-10-19", commit="8a1ed9e8d35dfad26fb973996319965e4224dcdd")
    +    version("2020-10-19", commit="8a1ed9e8d35dfad26fb973996319965e4224dcdd", deprecated=True)
     
    +    depends_on("c", type="build")
         depends_on("cxx", type="build")
     
         variant("cuda", default=True, description="Build with CUDA")
     
         # Based on the table of the readme on github
         variant(
    -        "permutation_search_cuda", default=False, description="Build permutation search module"
    +        "permutation_search_cuda", default=True, description="Build permutation search module"
         )
    -    variant("bnp", default=False, description="Build batch norm module")
    -    variant("xentropy", default=False, description="Build cross entropy module")
    -    variant("focal_loss_cuda", default=False, description="Build focal loss module")
    -    variant("fused_index_mul_2d", default=False, description="Build fused_index_mul_2d module")
    -    variant("fast_layer_norm", default=False, description="Build fast layer norm module")
    -    variant("fmhalib", default=False, description="Build fmha module")
    +    variant("bnp", default=True, description="Build batch norm module")
    +    variant("xentropy", default=True, description="Build cross entropy module")
    +    variant("focal_loss", default=True, description="Build focal loss module")
    +    variant("index_mul_2d", default=True, description="Build fused_index_mul_2d module")
    +    variant("fast_layer_norm", default=True, description="Build fast layer norm module")
    +    variant("fmha", default=True, description="Build fmha module")
         variant(
    -        "fast_multihead_attn", default=False, description="Build fast multihead attention module"
    +        "fast_multihead_attn", default=True, description="Build fast multihead attention module"
         )
    -    variant("transducer", default=False, description="Build transducer module")
    -    variant("cudnn_gbn_lib", default=False, description="Build cudnn gbn module")
    -    variant("peer_memory_cuda", default=False, description="Build peer memory module")
    -    variant("nccl_p2p_cuda", default=False, description="Build with nccl p2p")
    -    variant("fast_bottleneck", default=False, description="Build fast_bottleneck module")
    -    variant("fused_conv_bias_relu", default=False, description="Build fused_conv_bias_relu moduel")
    +    variant("transducer", default=True, description="Build transducer module")
    +    variant("cudnn_gbn", default=True, description="Build cudnn gbn module")
    +    variant("peer_memory", default=True, description="Build peer memory module")
    +    variant("nccl_p2p", default=True, description="Build with nccl p2p")
    +    variant("fast_bottleneck", default=True, description="Build fast_bottleneck module")
    +    variant("fused_conv_bias_relu", default=True, description="Build fused_conv_bias_relu moduel")
    +    variant("distributed_adam", when="+cuda", default=True, description="CUDA kernels for multi-tensor Adam optimizer")
    +    variant("distributed_lamb", when="+cuda", default=True, description="CUDA kernels for multi-tensor Lamb optimizer")
    +    variant("permutation_search", when="+cuda", default=True, description="CUDA kernels for permutation search")
    +    variant("focal_loss", when="+cuda", default=True, description="CUDA kernels for focal loss")
    +    variant("group_norm", when="+cuda", default=True, description="CUDA kernels for group normalization")
    +    variant("index_mul_2d", when="+cuda", default=True, description="CUDA kernels for index mul calculations")
    +    variant("deprecated_fused_adam", when="+cuda", default=False, description="CUDA kernels for fused Adam optimizer")
    +    variant("deprecated_fused_lamb", when="+cuda", default=False, description="CUDA kernels for fused Lamb optimizer")
    +    variant("nccl_allocator", when="+cuda", default=True, description="NCCL allocator support")
    +    variant("gpu_direct_storage", when="+cuda", default=True, description="GPU direct storage support")
     
         requires(
    -        "+peer_memory_cuda+nccl_p2p_cuda",
    +        "+peer_memory+nccl_p2p",
             when="+fast_bottleneck",
    -        msg="+fast_bottleneck requires both +peer_memory_cuda and +nccl_p2p_cuda to be enabled.",
    +        msg="+fast_bottleneck requires both +peer_memory and +nccl_p2p to be enabled.",
         )
    -    requires("^cudnn@8.5:", when="+cudnn_gbn_lib")
    -    requires("^cudnn@8.4:", when="+fused_conv_bias_relu")
    -    requires("^nccl@2.10:", when="+nccl_p2p_cuda")
    -
         with default_args(type=("build")):
             depends_on("py-setuptools")
             depends_on("py-packaging")
             depends_on("py-pip")
    +        depends_on("ninja")
         with default_args(type=("build", "run")):
             depends_on("python@3:")
             depends_on("py-torch@0.4:")
             for _arch in CudaPackage.cuda_arch_values:
                 depends_on(f"py-torch+cuda cuda_arch={_arch}", when=f"+cuda cuda_arch={_arch}")
    +    with default_args(type=("build", "link", "run")):
    +        depends_on("py-pybind11")
    +        depends_on("cudnn@8.5:", when="+cudnn_gbn")
    +        depends_on("cudnn@8.4:", when="+fast_bottleneck")
    +        depends_on("cudnn@8.4:", when="+fused_conv_bias_relu")
    +        depends_on("nccl@2.10.3:", when="+nccl_p2p")
    +        depends_on("nccl@2.19:", when="+nccl_allocator")
     
    -    depends_on("py-pybind11", type=("build", "link", "run"))
         depends_on("cuda@9:", when="+cuda")
    +    depends_on("cuda@11:", when="+fmha")
     
         # https://github.com/NVIDIA/apex/issues/1498
         # https://github.com/NVIDIA/apex/pull/1499
         patch("1499.patch", when="@2020-10-19")
    +    patch(
    +        "https://github.com/NVIDIA/apex/pull/1879.patch?full_index=1",
    +        sha256="8e2e21aa883d93e6c0ea0fecb812c8de906b2e77bcffeeb716adabd1dd76650e",
    +        when="@23.05:2019",
    +    )
    +
    +    patch(
    +        "https://github.com/NVIDIA/apex/pull/1855.patch?full_index=1",
    +        sha256="8481b1234a9ce1e8bef4e57a259d8528107761e1843777489e815ec3727397fd",
    +        when="@:24.10",
    +    )
     
         conflicts(
             "cuda_arch=none",
    @@ -103,81 +133,70 @@ def setup_run_environment(self, env):
         @when("^py-pip@:23.0")
         def global_options(self, spec, prefix):
             args = []
    +        variant_to_arg = lambda v: args.append(f"--{v}") if spec.satisfies(f"+{v}") else None
             if spec.satisfies("^py-torch@1.0:"):
                 args.append("--cpp_ext")
                 if spec.satisfies("+cuda"):
                     args.append("--cuda_ext")
    -
    -        if spec.satisfies("+permutation_search_cuda"):
    -            args.append("--permutation_search")
    -        if spec.satisfies("+bnp"):
    -            args.append("--bnp")
    -        if spec.satisfies("+xentropy"):
    -            args.append("--xentropy")
    -        if spec.satisfies("+focal_loss_cuda"):
    -            args.append("--focal_loss")
    -        if spec.satisfies("+fused_index_mul_2d"):
    -            args.append("--index_mul_2d")
    -        if spec.satisfies("+fast_layer_norm"):
    -            args.append("--fast_layer_norm")
    -        if spec.satisfies("+fmhalib"):
    -            args.append("--fmha")
    -        if spec.satisfies("+fast_multihead_attn"):
    -            args.append("--fast_multihead_attn")
    -        if spec.satisfies("+transducer"):
    -            args.append("--transducer")
    -        if spec.satisfies("+cudnn_gbn_lib"):
    -            args.append("--cudnn_gbn")
    -        if spec.satisfies("+peer_memory_cuda"):
    -            args.append("--peer_memory")
    -        if spec.satisfies("+nccl_p2p_cuda"):
    -            args.append("--nccl_p2p")
    -        if spec.satisfies("+fast_bottleneck"):
    -            args.append("--fast_bottleneck")
    -        if spec.satisfies("+fused_conv_bias_relu"):
    -            args.append("--fused_conv_bias_relu")
    -
    +                variant_to_arg("distributed_adam")
    +                variant_to_arg("distributed_lamb")
    +                variant_to_arg("permutation_search")
    +                variant_to_arg("bnp")
    +                variant_to_arg("xentropy")
    +                variant_to_arg("focal_loss")
    +                variant_to_arg("group_norm")
    +                variant_to_arg("index_mul_2d")
    +                variant_to_arg("deprecated_fused_adam")
    +                variant_to_arg("deprecated_fused_lamb")
    +                variant_to_arg("fast_layer_norm")
    +                variant_to_arg("fmha")
    +                variant_to_arg("fast_multihead_attn")
    +                variant_to_arg("transducer")
    +                variant_to_arg("cudnn_gbn")
    +                variant_to_arg("peer_memory")
    +                variant_to_arg("nccl_p2p")
    +                variant_to_arg("fast_bottleneck")
    +                variant_to_arg("fused_conv_bias_relu")
    +                variant_to_arg("nccl_allocator")
    +                variant_to_arg("gpu_direct_storage")
             return args
     
         @when("^py-pip@23.1:")
         def config_settings(self, spec, prefix):
    -        global_options = ""
    +        args = ""
    +        
    +        def variant_to_arg(v):
    +            nonlocal args
    +            if spec.satisfies(f"+{v}"):
    +                args += f" --{v}"
    +        
             if spec.satisfies("^py-torch@1.0:"):
    -            global_options += "--cpp_ext"
    +            args="--cpp_ext"
                 if spec.satisfies("+cuda"):
    -                global_options += " --cuda_ext"
    -
    -        if spec.satisfies("+permutation_search_cuda"):
    -            global_options += " --permutation_search"
    -        if spec.satisfies("+bnp"):
    -            global_options += " --bnp"
    -        if spec.satisfies("+xentropy"):
    -            global_options += " --xentropy"
    -        if spec.satisfies("+focal_loss_cuda"):
    -            global_options += " --focal_loss"
    -        if spec.satisfies("+fused_index_mul_2d"):
    -            global_options += " --index_mul_2d"
    -        if spec.satisfies("+fast_layer_norm"):
    -            global_options += " --fast_layer_norm"
    -        if spec.satisfies("+fmhalib"):
    -            global_options += " --fmha"
    -        if spec.satisfies("+fast_multihead_attn"):
    -            global_options += " --fast_multihead_attn"
    -        if spec.satisfies("+transducer"):
    -            global_options += " --transducer"
    -        if spec.satisfies("+cudnn_gbn_lib"):
    -            global_options += " --cudnn_gbn"
    -        if spec.satisfies("+peer_memory_cuda"):
    -            global_options += " --peer_memory"
    -        if spec.satisfies("+nccl_p2p_cuda"):
    -            global_options += " --nccl_p2p"
    -        if spec.satisfies("+fast_bottleneck"):
    -            global_options += " --fast_bottleneck"
    -        if spec.satisfies("+fused_conv_bias_relu"):
    -            global_options += " --fused_conv_bias_relu"
    -
    +                args += " --cuda_ext"
    +                variant_to_arg("distributed_adam")
    +                variant_to_arg("distributed_lamb")
    +                variant_to_arg("permutation_search")
    +                variant_to_arg("bnp")
    +                variant_to_arg("xentropy")
    +                variant_to_arg("focal_loss")
    +                variant_to_arg("group_norm")
    +                variant_to_arg("index_mul_2d")
    +                variant_to_arg("deprecated_fused_adam")
    +                variant_to_arg("deprecated_fused_lamb")
    +                variant_to_arg("fast_layer_norm")
    +                variant_to_arg("fmha")
    +                variant_to_arg("fast_multihead_attn")
    +                variant_to_arg("transducer")
    +                variant_to_arg("cudnn_gbn")
    +                variant_to_arg("peer_memory")
    +                variant_to_arg("nccl_p2p")
    +                variant_to_arg("fast_bottleneck")
    +                variant_to_arg("fused_conv_bias_relu")
    +                variant_to_arg("nccl_allocator")
    +                variant_to_arg("gpu_direct_storage")
             return {
                 "builddir": "build",
                 "compile-args": f"-j{make_jobs}",
    -            "--global-option": global_options,
    +            "--build-option": args,
             }
    diff --git c/var/spack/repos/builtin/packages/py-torch/package.py i/var/spack/repos/builtin/packages/py-torch/package.py
    index e2bc15b64e..86a9570363 100644
    --- c/var/spack/repos/builtin/packages/py-torch/package.py
    +++ i/var/spack/repos/builtin/packages/py-torch/package.py
    @@ -25,6 +25,7 @@ class PyTorch(PythonPackage, CudaPackage, ROCmPackage):
         maintainers("adamjstewart")
     
         version("main", branch="main")
    +    version("2.6.0", tag="v2.6.0", commit="1eba9b3aa3c43f86f4a2c807ac8e12c4a7767340")
         version("2.5.1", tag="v2.5.1", commit="a8d6afb511a69687bbb2b7e88a3cf67917e1697e")
         version("2.5.0", tag="v2.5.0", commit="32f585d9346e316e554c8d9bf7548af9f62141fc")
         version("2.4.1", tag="v2.4.1", commit="ee1b6804381c57161c477caa380a840a84167676")
    @@ -156,8 +157,10 @@ class PyTorch(PythonPackage, CudaPackage, ROCmPackage):
         with default_args(type=("build", "run")):
             # setup.py
             depends_on("py-filelock", when="@2:")
    +        depends_on("py-typing-extensions@4.10:", when="@2.6:")
             depends_on("py-typing-extensions@4.8:", when="@2.2:")
             depends_on("py-typing-extensions@3.6.2.1:", when="@1.7:")
    +        depends_on("py-sympy@1.13.1", when="@2.5:")
             depends_on("py-sympy", when="@2:")
             depends_on("py-networkx", when="@2:")
             depends_on("py-jinja2", when="@2:")
    @@ -166,7 +169,7 @@ class PyTorch(PythonPackage, CudaPackage, ROCmPackage):
             # pyproject.toml
             depends_on("py-setuptools")
             depends_on("py-astunparse", when="@1.13:")
    -        depends_on("py-numpy@1.16.6:")
    +        depends_on("py-numpy")
             # https://github.com/pytorch/pytorch/issues/107302
             depends_on("py-numpy@:1", when="@:2.2")
             depends_on("py-pyyaml")
    @@ -180,6 +183,7 @@ class PyTorch(PythonPackage, CudaPackage, ROCmPackage):
         # Third party dependencies
         depends_on("fp16@2020-05-14", when="@1.6:")
         depends_on("fxdiv@2020-04-17", when="@1.6:")
    +    depends_on("nvtx@3.1.0", when="@2.6:")
         # https://github.com/pytorch/pytorch/issues/60332
         # depends_on("xnnpack@2024-02-29", when="@2.3:+xnnpack")
         # depends_on("xnnpack@2022-12-21", when="@2.0:2.2+xnnpack")
    @@ -188,7 +192,8 @@ class PyTorch(PythonPackage, CudaPackage, ROCmPackage):
         # depends_on("xnnpack@2021-02-22", when="@1.8:1.9+xnnpack")
         # depends_on("xnnpack@2020-03-23", when="@1.6:1.7+xnnpack")
         depends_on("benchmark", when="@1.6:+test")
    -    depends_on("cpuinfo@2024-09-06", when="@2.5.1:")
    +    depends_on("cpuinfo@2024-09-26", when="@2.6:")
    +    depends_on("cpuinfo@2024-09-06", when="@2.5.1")
         depends_on("cpuinfo@2024-08-30", when="@2.5.0")
         depends_on("cpuinfo@2023-11-04", when="@2.3:2.4")
         depends_on("cpuinfo@2023-01-13", when="@2.1:2.2")
    @@ -208,6 +213,7 @@ class PyTorch(PythonPackage, CudaPackage, ROCmPackage):
         depends_on("gloo+libuv", when="@1.6: platform=darwin")
         depends_on("nccl", when="+nccl+cuda")
         # https://github.com/pytorch/pytorch/issues/60331
    +    # depends_on("onnx@1.17.0", when="@2.6:+onnx_ml")
         # depends_on("onnx@1.16.0", when="@2.3:+onnx_ml")
         # depends_on("onnx@1.15.0", when="@2.2+onnx_ml")
         # depends_on("onnx@1.14.1", when="@2.1+onnx_ml")
    @@ -234,7 +240,8 @@ class PyTorch(PythonPackage, CudaPackage, ROCmPackage):
         depends_on("pthreadpool@2020-10-05", when="@1.8")
         depends_on("pthreadpool@2020-06-15", when="@1.6:1.7")
         with default_args(type=("build", "link", "run")):
    -        depends_on("py-pybind11@2.13.5:", when="@2.5:")
    +        depends_on("py-pybind11@2.13.6:", when="@2.6:")
    +        depends_on("py-pybind11@2.13.5:", when="@2.5:2.5.1")
             depends_on("py-pybind11@2.12.0:", when="@2.3:2.4")
             depends_on("py-pybind11@2.11.0:", when="@2.1:2.2")
             depends_on("py-pybind11@2.10.1:", when="@2.0")
    @@ -258,7 +265,7 @@ class PyTorch(PythonPackage, CudaPackage, ROCmPackage):
             depends_on("cuda@9:11.4", when="@:1.5+cuda")
         # https://github.com/pytorch/pytorch#prerequisites
         # https://github.com/pytorch/pytorch/issues/119400
    -    depends_on("cudnn@8.5:9.0", when="@2.3:+cudnn")
    +    depends_on("cudnn@8.5:", when="@2.3:+cudnn")
         depends_on("cudnn@7:8", when="@1.6:2.2+cudnn")
         depends_on("cudnn@7", when="@:1.5+cudnn")
         depends_on("magma+cuda", when="+magma+cuda")
    @@ -301,6 +308,14 @@ class PyTorch(PythonPackage, CudaPackage, ROCmPackage):
     
         conflicts("%gcc@:9.3", when="@2.2:", msg="C++17 support required")
     
    +    # https://github.com/pytorch/pytorch/issues/146239
    +    patch(
    +        "https://github.com/pytorch/pytorch/pull/140275.patch?full_index=1",
    +        sha256="65f56305a27d47d7065711d1131c6ac1611fabcb55b129c27ed6beabe4b94fe0",
    +        when="@2.6:",
    +        reverse=True,
    +    )
    +
         # https://github.com/pytorch/pytorch/issues/90448
         patch(
             "https://github.com/pytorch/pytorch/pull/97270.patch?full_index=1",
    @@ -335,6 +350,9 @@ class PyTorch(PythonPackage, CudaPackage, ROCmPackage):
         # https://github.com/pytorch/pytorch/pull/35607
         # https://github.com/pytorch/pytorch/pull/37865
         patch("xnnpack.patch", when="@1.5")
    +    # https://github.com/pytorch/pytorch/issues/141083
    +    # https://github.com/google/XNNPACK/commit/5f23827e66cca435fa400b6e221892ac95af0079
    +    patch("xnnpack2.patch", when="@2.6", working_dir="third_party/XNNPACK")
     
         # Fixes build error when ROCm is enabled for pytorch-1.5 release
         patch("rocm.patch", when="@1.5+rocm")
    @@ -571,7 +589,8 @@ def enable_or_disable(variant, keyword="USE", var=None):
             # Flash attention has very high memory requirements that may cause the build to fail
             # https://github.com/pytorch/pytorch/issues/111526
             # https://github.com/pytorch/pytorch/issues/124018
    -        env.set("USE_FLASH_ATTENTION", "OFF")
    +        env.set("USE_FLASH_ATTENTION", "ON")
    +        env.set("USE_MEM_EFF_ATTENTION", "ON")
     
             enable_or_disable("fbgemm")
             enable_or_disable("kineto")
    @@ -669,6 +688,7 @@ def enable_or_disable(variant, keyword="USE", var=None):
             env.set("USE_SYSTEM_FXDIV", "ON")
             env.set("USE_SYSTEM_GLOO", "ON")
             env.set("USE_SYSTEM_NCCL", "ON")
    +        env.set("USE_SYSTEM_NVTX", "ON")
             # https://github.com/pytorch/pytorch/issues/60331
             # env.set("USE_SYSTEM_ONNX", "ON")
             env.set("USE_SYSTEM_PSIMD", "ON")
    diff --git c/var/spack/repos/builtin/packages/py-torch/xnnpack2.patch i/var/spack/repos/builtin/packages/py-torch/xnnpack2.patch
    new file mode 100644
    index 0000000000..d3e0860b30
    --- /dev/null
    +++ i/var/spack/repos/builtin/packages/py-torch/xnnpack2.patch
    @@ -0,0 +1,34 @@
    +diff --git a/src/reference/unary-elementwise.cc b/src/reference/unary-elementwise.cc
    +index bd95ded6c..da892d8be 100644
    +--- a/src/reference/unary-elementwise.cc
    ++++ b/src/reference/unary-elementwise.cc
    +@@ -127,6 +127,16 @@ struct ConvertOp {
    +   }
    + };
    + 
    ++#ifdef XNN_HAVE_FLOAT16
    ++template <>
    ++struct ConvertOp<xnn_bfloat16, _Float16> {
    ++  explicit ConvertOp(const xnn_unary_uparams*) {}
    ++  _Float16 operator()(xnn_bfloat16 x) const {
    ++    return static_cast<_Float16>(static_cast<float>(x));
    ++  }
    ++};
    ++#endif
    ++
    + template <typename TIn, typename TOut>
    + const xnn_unary_elementwise_config* get_convert_config(
    +     std::true_type /*input_quantized*/, std::true_type /*output_quantized*/) {
    +diff --git a/src/xnnpack/simd/s16-neon.h b/src/xnnpack/simd/s16-neon.h
    +index 4e8ebcfbd..e8392f4e9 100644
    +--- a/src/xnnpack/simd/s16-neon.h
    ++++ b/src/xnnpack/simd/s16-neon.h
    +@@ -70,7 +70,7 @@ static XNN_INLINE void xnn_store_tail_s16(int16_t* output, xnn_simd_s16_t v,
    +     v_low = vget_high_s16(v);
    +   }
    +   if (num_elements & 2) {
    +-    vst1_lane_s32((void*) output, vreinterpret_s32_s16(v_low), 0);
    ++    vst1_lane_s32((int32_t*) output, vreinterpret_s32_s16(v_low), 0);
    +     output += 2;
    +     v_low = vext_s16(v_low, v_low, 2);
    +   }
    diff --git c/var/spack/repos/builtin/packages/py-torchaudio/package.py i/var/spack/repos/builtin/packages/py-torchaudio/package.py
    index 59a7e2825b..178556b609 100644
    --- c/var/spack/repos/builtin/packages/py-torchaudio/package.py
    +++ i/var/spack/repos/builtin/packages/py-torchaudio/package.py
    @@ -18,6 +18,7 @@ class PyTorchaudio(PythonPackage):
         maintainers("adamjstewart")
     
         version("main", branch="main")
    +    version("2.6.0", tag="v2.6.0", commit="d8831425203385077a03c1d92cfbbe3bf2106008")
         version("2.5.1", tag="v2.5.1", commit="1661daf10599ca8889f092ec37814fabbe202bb0")
         version("2.5.0", tag="v2.5.0", commit="56bc006d56a0d4960de6a1e0b6340cba4eda05cd")
         version("2.4.1", tag="v2.4.1", commit="e8cbe17769796ce963fbc71b8990f1474774e6d2")
    @@ -57,7 +58,8 @@ class PyTorchaudio(PythonPackage):
     
         with default_args(type=("build", "link", "run")):
             # Based on PyPI wheel availability
    -        depends_on("python@3.9:3.12", when="@2.5:")
    +        depends_on("python@3.9:3.13", when="@2.6:")
    +        depends_on("python@3.9:3.12", when="@2.5")
             depends_on("python@3.8:3.12", when="@2.2:2.4")
             depends_on("python@3.8:3.11", when="@2.0:2.1")
             depends_on("python@:3.10", when="@0.12:0")
    @@ -65,6 +67,7 @@ class PyTorchaudio(PythonPackage):
             depends_on("python@:3.8", when="@:0.7.0")
     
             depends_on("py-torch@main", when="@main")
    +        depends_on("py-torch@2.6.0", when="@2.6.0")
             depends_on("py-torch@2.5.1", when="@2.5.1")
             depends_on("py-torch@2.5.0", when="@2.5.0")
             depends_on("py-torch@2.4.1", when="@2.4.1")
    @@ -117,7 +120,7 @@ class PyTorchaudio(PythonPackage):
         patch(
             "https://github.com/pytorch/audio/pull/3811.patch?full_index=1",
             sha256="34dce3403abb03f62827e8a1efcdb2bf7742477a01f155ebb9c7fefe9588b132",
    -        when="@2.2:",
    +        when="@2.2:2.5",
         )
         conflicts("^cuda@12.5:", when="@:2.1")
     
    diff --git c/var/spack/repos/builtin/packages/py-torchvision/package.py i/var/spack/repos/builtin/packages/py-torchvision/package.py
    index 4fe32d63cc..34366160fc 100644
    --- c/var/spack/repos/builtin/packages/py-torchvision/package.py
    +++ i/var/spack/repos/builtin/packages/py-torchvision/package.py
    @@ -19,6 +19,7 @@ class PyTorchvision(PythonPackage):
         license("BSD-3-Clause")
     
         version("main", branch="main")
    +    version("0.21.0", sha256="0a4a967bbb7f9810f792cd0289a07fb98c8fb5d1303fae8b63e3a6b05d720058")
         version("0.20.1", sha256="7e08c7f56e2c89859310e53d898f72bccc4987cd83e08cfd6303513da15a9e71")
         version("0.20.0", sha256="b59d9896c5c957c6db0018754bbd17d079c5102b82b9be0b438553b40a7b6029")
         version("0.19.1", sha256="083e75c467285595ec3eb3c7aa8493c19e53d7eb42f13046fb56a07c8897e5a8")
    @@ -61,8 +62,6 @@ class PyTorchvision(PythonPackage):
         variant("png", default=True, description=desc.format("PNG"))
         variant("jpeg", default=True, description=desc.format("JPEG"))
         variant("webp", default=False, description=desc.format("WEBP"), when="@0.20:")
    -    variant("heic", default=False, description=desc.format("HEIC"), when="@0.20:")
    -    variant("avif", default=False, description=desc.format("AVIF"), when="@0.20:")
         variant("nvjpeg", default=False, description=desc.format("NVJPEG"))
         variant("video_codec", default=False, description=desc.format("video_codec"))
         variant("ffmpeg", default=False, description=desc.format("FFMPEG"))
    @@ -73,8 +72,8 @@ class PyTorchvision(PythonPackage):
     
         with default_args(type=("build", "link", "run")):
             # Based on PyPI wheel availability
    -        depends_on("python@3.9:3.12", when="@0.20:")
    -        depends_on("python@3.8:3.12", when="@0.17:0.19")
    +        depends_on("python@3.9:3.13", when="@0.21:")
    +        depends_on("python@3.8:3.12", when="@0.17:0.20")
             depends_on("python@3.8:3.11", when="@0.15:0.16")
             depends_on("python@:3.10", when="@0.12:0.14")
             depends_on("python@:3.9", when="@0.8.2:0.11")
    @@ -82,6 +81,7 @@ class PyTorchvision(PythonPackage):
     
             # https://github.com/pytorch/vision#installation
             depends_on("py-torch@main", when="@main")
    +        depends_on("py-torch@2.6.0", when="@0.21.0")
             depends_on("py-torch@2.5.1", when="@0.20.1")
             depends_on("py-torch@2.5.0", when="@0.20.0")
             depends_on("py-torch@2.4.1", when="@0.19.1")
    @@ -132,8 +132,6 @@ class PyTorchvision(PythonPackage):
         depends_on("libpng@1.6:", when="+png")
         depends_on("jpeg", when="+jpeg")
         depends_on("libwebp", when="+webp")
    -    depends_on("libheif", when="+heic")
    -    depends_on("libavif", when="+avif")
         depends_on("cuda", when="+nvjpeg")
         depends_on("cuda", when="+video_codec")
         depends_on("ffmpeg@3.1:", when="+ffmpeg")
    @@ -190,7 +188,7 @@ def setup_build_environment(self, env):
             for gpu in ["cuda", "mps"]:
                 env.set(f"FORCE_{gpu.upper()}", int(f"+{gpu}" in self.spec["py-torch"]))
     
    -        extensions = ["png", "jpeg", "webp", "heic", "avif", "nvjpeg", "video_codec", "ffmpeg"]
    +        extensions = ["png", "jpeg", "webp", "nvjpeg", "video_codec", "ffmpeg"]
             for extension in extensions:
                 env.set(f"TORCHVISION_USE_{extension.upper()}", int(f"+{extension}" in self.spec))
     
    diff --git c/var/spack/repos/builtin/packages/py-transformer-engine/package.py i/var/spack/repos/builtin/packages/py-transformer-engine/package.py
    index 175b333626..9ab178e815 100644
    --- c/var/spack/repos/builtin/packages/py-transformer-engine/package.py
    +++ i/var/spack/repos/builtin/packages/py-transformer-engine/package.py
    @@ -6,7 +6,7 @@
     from spack.package import *
     
     
    -class PyTransformerEngine(PythonPackage):
    +class PyTransformerEngine(PythonPackage, CudaPackage):
         """
         A library for accelerating Transformer models on NVIDIA GPUs, including fp8 precision on Hopper
         GPUs.
    @@ -26,25 +26,33 @@ class PyTransformerEngine(PythonPackage):
     
         variant("userbuffers", default=True, description="Enable userbuffers, this option needs MPI.")
     
    -    depends_on("py-setuptools", type="build")
    -    depends_on("cmake@3.18:")
    -    depends_on("py-pydantic")
    -    depends_on("py-importlib-metadata")
    +    patch("python_v3.13.patch", when="@main")
     
    -    with default_args(type=("build", "run")):
    -        depends_on("py-accelerate")
    -        depends_on("py-datasets")
    -        depends_on("py-flash-attn@2.2:2.4.2")
    -        depends_on("py-packaging")
    -        depends_on("py-torchvision")
    -        depends_on("py-transformers")
    -        depends_on("mpi", when="+userbuffers")
    +    with default_args(type=("build")):
    +        depends_on("py-setuptools")
    +        depends_on("cmake@3.21:")
    +        depends_on("ninja")
     
    +    with default_args(type=("build", "link")):
    +        depends_on("py-pybind11")
    +    
         with default_args(type=("build", "link", "run")):
    +        depends_on("py-pydantic")
    +        depends_on("py-importlib-metadata@1:")
    +        depends_on("py-packaging")
             depends_on("py-torch+cuda+cudnn")
    +        depends_on("cudnn")
    +        depends_on("mpi", when="+userbuffers")
     
         def setup_build_environment(self, env):
             env.set("NVTE_FRAMEWORK", "pytorch")
    +        env.set("CUDNN_PATH", self.spec["cudnn"].prefix)
    +        env.set("CUDNN_HOME", self.spec["cudnn"].prefix)
    +        env.set("CUDNN_ROOT", self.spec["cudnn"].prefix)
    +        env.prepend_path("CPLUS_INCLUDE_PATH", self.spec["cudnn"].prefix.include)
             if self.spec.satisfies("+userbuffers"):
                 env.set("NVTE_WITH_USERBUFFERS", "1")
    +            env.set("NVTE_UB_WITH_MPI", "1")
                 env.set("MPI_HOME", self.spec["mpi"].prefix)
    +        arch_str = ";".join(self.spec.variants["cuda_arch"].value)
    +        env.set("CUDAARCHS", arch_str)
    diff --git c/var/spack/repos/builtin/packages/py-transformer-engine/python_v3.13.patch i/var/spack/repos/builtin/packages/py-transformer-engine/python_v3.13.patch
    new file mode 100644
    index 0000000000..f24c699de3
    --- /dev/null
    +++ i/var/spack/repos/builtin/packages/py-transformer-engine/python_v3.13.patch
    @@ -0,0 +1,20 @@
    +diff --git i/setup.py w/setup.py
    +index 1d98184..6fcf0d5 100644
    +--- i/setup.py
    ++++ w/setup.py
    +@@ -184,13 +184,14 @@ if __name__ == "__main__":
    +         long_description_content_type="text/x-rst",
    +         ext_modules=ext_modules,
    +         cmdclass={"build_ext": CMakeBuildExtension, "bdist_wheel": TimedBdist},
    +-        python_requires=">=3.8, <3.13",
    ++        python_requires=">=3.8, <3.14",
    +         classifiers=[
    +             "Programming Language :: Python :: 3.8",
    +             "Programming Language :: Python :: 3.9",
    +             "Programming Language :: Python :: 3.10",
    +             "Programming Language :: Python :: 3.11",
    +             "Programming Language :: Python :: 3.12",
    ++            "Programming Language :: Python :: 3.13",
    +         ],
    +         setup_requires=setup_requires,
    +         install_requires=install_requires,
    diff --git c/var/spack/repos/builtin/packages/py-transformers/package.py i/var/spack/repos/builtin/packages/py-transformers/package.py
    index fc4a35ae49..557106aa52 100644
    --- c/var/spack/repos/builtin/packages/py-transformers/package.py
    +++ i/var/spack/repos/builtin/packages/py-transformers/package.py
    @@ -18,6 +18,7 @@ class PyTransformers(PythonPackage):
     
         license("Apache-2.0")
     
    +    version("4.48.3", sha256="a5e8f1e9a6430aa78215836be70cecd3f872d99eeda300f41ad6cc841724afdb")
         version("4.42.3", sha256="7539873ff45809145265cbc94ea4619d2713c41ceaa277b692d8b0be3430f7eb")
         version("4.38.1", sha256="86dc84ccbe36123647e84cbd50fc31618c109a41e6be92514b064ab55bf1304c")
         version("4.35.2", sha256="2d125e197d77b0cdb6c9201df9fa7e2101493272e448b9fba9341c695bee2f52")
    @@ -33,14 +34,16 @@ class PyTransformers(PythonPackage):
     
         with default_args(type=("build", "run")):
             depends_on("py-filelock")
    +        depends_on("py-huggingface-hub@0.24.0:", when="@4.48.3:")
             depends_on("py-huggingface-hub@0.23.2:", when="@4.42.3:")
             depends_on("py-huggingface-hub@0.19.3:", when="@4.38.1:")
             depends_on("py-huggingface-hub@0.16.4:0", when="@4.34:")
             depends_on("py-huggingface-hub@0.14.1:0", when="@4.26:")
             depends_on("py-huggingface-hub@0.10:0", when="@4.24:")
             depends_on("py-huggingface-hub@0.0.8", when="@4.6.1")
    -        depends_on("py-numpy@1.17:1", when="@4.6:")
    -        depends_on("py-numpy@:1")
    +        depends_on("py-numpy@1.17:", when="@4.48.3:")
    +        depends_on("py-numpy@1.17:1", when="@4.6:4.48.0")
    +        depends_on("py-numpy@:1", when="@:4.48.0")
             depends_on("py-packaging@20:", when="@4.24:")
             depends_on("py-packaging", when="@4.6.1")
             depends_on("py-pyyaml@5.1:", when="@4.24:")
    @@ -48,7 +51,8 @@ class PyTransformers(PythonPackage):
             depends_on("py-requests")
             depends_on("py-safetensors@0.4.1:", when="@4.38.1:")
             depends_on("py-safetensors@0.3.1:", when="@4.31:")
    -        depends_on("py-tokenizers@0.19", when="@4.40.0:")
    +        depends_on("py-tokenizers@0.21", when="@4.48.0:")
    +        depends_on("py-tokenizers@0.19", when="@4.40.0:4.48.0")
             depends_on("py-tokenizers@0.14:0.18", when="@4.35:4.39.3")
             depends_on("py-tokenizers@0.11.1:0.11.2,0.11.4:0.13", when="@4.24:4.33")
             depends_on("py-tokenizers@0.10.1:0.10", when="@4.6.1")
    diff --git c/var/spack/repos/builtin/packages/py-triton/package.py i/var/spack/repos/builtin/packages/py-triton/package.py
    index 0c326c44d4..fbf06c8dc7 100644
    --- c/var/spack/repos/builtin/packages/py-triton/package.py
    +++ i/var/spack/repos/builtin/packages/py-triton/package.py
    @@ -3,33 +3,84 @@
     #
     # SPDX-License-Identifier: (Apache-2.0 OR MIT)
     
    +import llnl.util.filesystem as fs
    +
    +from spack import build_systems
     from spack.package import *
     
     
     class PyTriton(PythonPackage):
         """A language and compiler for custom Deep Learning operations."""
     
    -    homepage = "https://github.com/openai/triton"
    -    url = "https://github.com/openai/triton/archive/refs/tags/v2.1.0.tar.gz"
    -    git = "https://github.com/openai/triton.git"
    +    homepage = "https://github.com/triton-lang/triton"
    +    url = "https://github.com/triton-lang/triton/archive/refs/tags/v2.1.0.tar.gz"
    +    git = "https://github.com/triton-lang/triton.git"
     
         license("MIT")
     
         version("main", branch="main")
    +    # new versions are no longer tagged and pypi does not provide source distributions
    +    version("3.2.0", commit="c802bb4fbe492b2d34405313a4f4d96d8f91a4d8")
    +    version("3.1.0", commit="5fe38ffd73c2ac6ed6323b554205186696631c6f")
         version("2.1.0", sha256="4338ca0e80a059aec2671f02bfc9320119b051f378449cf5f56a1273597a3d99")
     
         depends_on("c", type="build")  # generated
         depends_on("cxx", type="build")  # generated
     
    -    depends_on("py-setuptools@40.8:", type="build")
    -    depends_on("cmake@3.18:", type="build")
    +    with default_args(type="build"):
    +        depends_on("py-setuptools@40.8:")
    +        depends_on("cmake@3.18:")
    +        depends_on("ninja")
    +
    +    with default_args(type=("build", "link", "run")):
    +        depends_on("py-pybind11")
    +        depends_on("cuda")
    +
         depends_on("py-filelock", type=("build", "run"))
         depends_on("zlib-api", type="link")
    +
         conflicts("^openssl@3.3.0")
     
    +    # avoid bdist_whell.dist_info_dir problems:
    +    # pypa used to contain `bdist_wheel` but it is part of setuptools as of v70.1
    +    # these patches change
    +    #     wheel.bdist_wheel -> setuptools.command.bdist_wheel.bdist_wheel
    +    # see https://github.com/pypa/wheel/pull/631
    +    # and https://github.com/pypa/setuptools/pull/4684
    +    patch("setup_v3.1.0.patch", when="@3.1.0 ^py-setuptools@70.1:")
    +    patch("setup_v3.2.0.patch", when="@3.2.0 ^py-setuptools@70.1:")
    +
         def setup_build_environment(self, env):
             """Set environment variables used to control the build"""
             if self.spec.satisfies("%clang"):
                 env.set("TRITON_BUILD_WITH_CLANG_LLD", "True")
    +        # set number of concurrent build jobs
    +        env.set("MAX_JOBS", make_jobs)
    +        # add a directory for triton's downloads
    +        triton_home = f"{self.build_directory}/.triton_home"
    +        env.set("TRITON_HOME", triton_home)
    +        # use spack installed dependencies
    +        env.set("PYBIND11_SYSPATH", self.spec["py-pybind11"].prefix)
    +        env.set("TRITON_PTXAS_PATH", self.spec["cuda"].prefix)
    +        env.set("TRITON_CUOBJDUMP_PATH", self.spec["cuda"].prefix)
    +        env.set("TRITON_NVDISASM_PATH", self.spec["cuda"].prefix)
    +        env.set("TRITON_CUDACRT_PATH", self.spec["cuda"].prefix)
    +        env.set("TRITON_CUDART_PATH", self.spec["cuda"].prefix)
    +        cupti_path = self.spec["cuda"].prefix.extras.CUPTI
    +        env.set("TRITON_CUPTI_INCLUDE_PATH", f"{cupti_path}/include")
    +        env.set("TRITON_CUPTI_LIB_PATH", f"{cupti_path}/lib64")
    +
    +    # build_directory does not work since apparently one needs to call pip from
    +    # the parent directory
    +    #build_directory = "python"
     
    -    build_directory = "python"
    +# override pip install to use python subdirectory from parent directory
    +class PythonPipBuilder(build_systems.python.PythonPipBuilder):
    +    def install(self, pkg: PythonPackage, spec: Spec, prefix) -> None:
    +        pip = spec["python"].command
    +        pip.add_default_arg("-m", "pip")
    +        args = build_systems.python.PythonPipBuilder.std_args(pkg) + [f"--prefix={prefix}"]
    +        # build directory specified manually as additional argument to pip install
    +        args.append("./python")
    +        with fs.working_dir(self.build_directory):
    +            pip(*args)
    diff --git c/var/spack/repos/builtin/packages/py-triton/setup_v3.1.0.patch i/var/spack/repos/builtin/packages/py-triton/setup_v3.1.0.patch
    new file mode 100644
    index 0000000000..afda492a1a
    --- /dev/null
    +++ i/var/spack/repos/builtin/packages/py-triton/setup_v3.1.0.patch
    @@ -0,0 +1,36 @@
    +diff --git c/pyproject.toml i/pyproject.toml
    +index e1ecf8228..35c5426c3 100644
    +--- c/pyproject.toml
    ++++ i/pyproject.toml
    +@@ -1,5 +1,5 @@
    + [build-system]
    +-requires = ["setuptools>=40.8.0", "wheel", "cmake>=3.18", "ninja>=1.11.1"]
    ++requires = ["setuptools>=40.8.0", "cmake>=3.18", "ninja>=1.11.1"]
    + 
    + [tool.yapf]
    + based_on_style = "pep8"
    +diff --git c/python/pyproject.toml i/python/pyproject.toml
    +index 315aa7da9..97b61bcd4 100644
    +--- c/python/pyproject.toml
    ++++ i/python/pyproject.toml
    +@@ -1,6 +1,6 @@
    + 
    + [build-system]
    +-requires = ["setuptools>=40.8.0", "wheel", "cmake>=3.18", "ninja>=1.11.1"]
    ++requires = ["setuptools>=40.8.0", "cmake>=3.18", "ninja>=1.11.1"]
    + 
    + # We're incrementally switching from autopep8 to ruff.
    + [tool.autopep8]
    +diff --git c/python/setup.py i/python/setup.py
    +index c60dc6158..ad6f8edc9 100644
    +--- c/python/setup.py
    ++++ i/python/setup.py
    +@@ -22,7 +22,7 @@ from dataclasses import dataclass
    + from distutils.command.install import install
    + from setuptools.command.develop import develop
    + from setuptools.command.egg_info import egg_info
    +-from wheel.bdist_wheel import bdist_wheel
    ++from setuptools.command.bdist_wheel import bdist_wheel
    + 
    + 
    + @dataclass
    diff --git c/var/spack/repos/builtin/packages/py-triton/setup_v3.2.0.patch i/var/spack/repos/builtin/packages/py-triton/setup_v3.2.0.patch
    new file mode 100644
    index 0000000000..1e2c94e22f
    --- /dev/null
    +++ i/var/spack/repos/builtin/packages/py-triton/setup_v3.2.0.patch
    @@ -0,0 +1,36 @@
    +diff --git i/pyproject.toml w/pyproject.toml
    +index e1ecf8228..35c5426c3 100644
    +--- i/pyproject.toml
    ++++ w/pyproject.toml
    +@@ -1,5 +1,5 @@
    + [build-system]
    +-requires = ["setuptools>=40.8.0", "wheel", "cmake>=3.18", "ninja>=1.11.1"]
    ++requires = ["setuptools>=40.8.0", "cmake>=3.18", "ninja>=1.11.1"]
    + 
    + [tool.yapf]
    + based_on_style = "pep8"
    +diff --git i/python/pyproject.toml w/python/pyproject.toml
    +index d96af50a5..8ca340be9 100644
    +--- i/python/pyproject.toml
    ++++ w/python/pyproject.toml
    +@@ -1,6 +1,6 @@
    + 
    + [build-system]
    +-requires = ["setuptools>=40.8.0", "wheel", "cmake>=3.18", "ninja>=1.11.1", "pybind11>=2.13.1"]
    ++requires = ["setuptools>=40.8.0", "cmake>=3.18", "ninja>=1.11.1", "pybind11>=2.13.1"]
    + 
    + # We're incrementally switching from autopep8 to ruff.
    + [tool.autopep8]
    +diff --git i/python/setup.py w/python/setup.py
    +index 725ba0213..89e86824b 100644
    +--- i/python/setup.py
    ++++ w/python/setup.py
    +@@ -24,7 +24,7 @@ from dataclasses import dataclass
    + from distutils.command.install import install
    + from setuptools.command.develop import develop
    + from setuptools.command.egg_info import egg_info
    +-from wheel.bdist_wheel import bdist_wheel
    ++from setuptools.command.bdist_wheel import bdist_wheel
    + 
    + import pybind11
    + 
    diff --git c/var/spack/repos/builtin/packages/py-trove-classifiers/package.py i/var/spack/repos/builtin/packages/py-trove-classifiers/package.py
    index 605bf930a5..66a23825f8 100644
    --- c/var/spack/repos/builtin/packages/py-trove-classifiers/package.py
    +++ i/var/spack/repos/builtin/packages/py-trove-classifiers/package.py
    @@ -11,10 +11,11 @@ class PyTroveClassifiers(PythonPackage):
         on PyPI. Classifiers categorize projects per PEP 301."""
     
         homepage = "https://github.com/pypa/trove-classifiers"
    -    pypi = "trove-classifiers/trove-classifiers-2023.3.9.tar.gz"
    +    pypi = "trove-classifiers/trove_classifiers-2025.3.19.19.tar.gz"
     
         license("Apache-2.0")
     
    +    version("2025.3.19.19", sha256="98e9d396fe908d5f43b7454fa4c43d17cd0fdadf046f45fb38a5e3af8d959ecd")
         version("2023.8.7", sha256="c9f2a0a85d545e5362e967e4f069f56fddfd91215e22ffa48c66fb283521319a")
         version("2023.3.9", sha256="ee42f2f8c1d4bcfe35f746e472f07633570d485fab45407effc0379270a3bb03")
     
    diff --git c/var/spack/repos/builtin/packages/py-zarr/package.py i/var/spack/repos/builtin/packages/py-zarr/package.py
    index 7da4fce325..05f19732bb 100644
    --- c/var/spack/repos/builtin/packages/py-zarr/package.py
    +++ i/var/spack/repos/builtin/packages/py-zarr/package.py
    @@ -15,6 +15,7 @@ class PyZarr(PythonPackage):
     
         license("MIT")
     
    +    version("3.0.1", sha256="033859c5603dc9c29e53af494ede24b42f1b761d2bb625466990a3b8a9afb792")
         version("2.17.0", sha256="6390a2b8af31babaab4c963efc45bf1da7f9500c9aafac193f84cf019a7c66b0")
         version("2.10.2", sha256="5c6ae914ab9215631bb95c09e76b9b9b4fffa70fec0c7bca26b68387d858ebe2")
         version("2.6.1", sha256="fa7eac1e4ff47ff82d09c42bb4679e18e8a05a73ee81ce59cee6a441a210b2fd")
    @@ -22,21 +23,33 @@ class PyZarr(PythonPackage):
         version("2.4.0", sha256="53aa21b989a47ddc5e916eaff6115b824c0864444b1c6f3aaf4f6cf9a51ed608")
         version("2.3.2", sha256="c62d0158fb287151c978904935a177b3d2d318dea3057cfbeac8541915dfa105")
     
    -    depends_on("python@3.9:", type=("build", "run"), when="@2.17:")
    -    depends_on("python@3.7:3", type=("build", "run"), when="@2.10")
    -    depends_on("py-setuptools@64:", type="build", when="@2.17:")
    -    depends_on("py-setuptools@38.6.0:", type="build", when="@2.4.0:")
    -    depends_on("py-setuptools@18.0:", type="build")
    -    depends_on("py-setuptools-scm@1.5.5:", type="build")
    -    depends_on("py-asciitree", type=("build", "run"))
    -    depends_on("py-numpy@1.21.1:", type=("build", "run"), when="@2.17:")
    -    depends_on("py-numpy@1.7:", type=("build", "run"))
    -    # https://github.com/zarr-developers/zarr-python/issues/1818
    -    depends_on("py-numpy@:1", when="@:2.17", type=("build", "run"))
    -    depends_on("py-fasteners", type=("build", "run"))
    -    depends_on("py-numcodecs@0.10:", type=("build", "run"), when="@2.17:")
    -    depends_on("py-numcodecs@0.6.4:", type=("build", "run"), when="@2.4.0:")
    -    depends_on("py-numcodecs@0.6.2:", type=("build", "run"))
    -
    -    # Historical dependencies
    -    depends_on("py-msgpack", type=("build", "run"), when="@:2.3.2")
    +    with when("@:2"):
    +        depends_on("python@3.9:", type=("build", "run"), when="@2.17:")
    +        depends_on("python@3.7:3", type=("build", "run"), when="@2.10")
    +        depends_on("py-setuptools@64:", type="build", when="@2.17:")
    +        depends_on("py-setuptools@38.6.0:", type="build", when="@2.4.0:")
    +        depends_on("py-setuptools@18.0:", type="build")
    +        depends_on("py-setuptools-scm@1.5.5:", type="build")
    +
    +        depends_on("py-asciitree", type=("build", "run"))
    +        depends_on("py-numpy@1.21.1:", type=("build", "run"), when="@2.17:")
    +        depends_on("py-numpy@1.7:", type=("build", "run"))
    +        # https://github.com/zarr-developers/zarr-python/issues/1818
    +        depends_on("py-numpy@:1", when="@:2.17", type=("build", "run"))
    +        depends_on("py-fasteners", type=("build", "run"))
    +        depends_on("py-numcodecs@0.10:", type=("build", "run"), when="@2.17:")
    +        depends_on("py-numcodecs@0.6.4:", type=("build", "run"), when="@2.4.0:")
    +        depends_on("py-numcodecs@0.6.2:", type=("build", "run"))
    +
    +        # Historical dependencies
    +        depends_on("py-msgpack", type=("build", "run"), when="@:2.3.2")
    +
    +    with when("@3:"):
    +        depends_on("python@3.11:", type=("build", "run"))
    +        depends_on("py-hatchling", type="build")
    +        depends_on("py-hatch-vcs", type="build")
    +        depends_on("py-packaging@22:", type=("build", "run"))
    +        depends_on("py-numpy@0.14:", type=("build", "run"))
    +        depends_on("py-numcodecs@0.14:", type=("build", "run"))
    +        depends_on("py-typing-extensions@4.9:", type=("build", "run"))
    +        depends_on("py-donfig@0.8:", type=("build", "run"))
    diff --git c/var/spack/repos/builtin/packages/sentencepiece/package.py i/var/spack/repos/builtin/packages/sentencepiece/package.py
    index a954519ece..fbce4ee94d 100644
    --- c/var/spack/repos/builtin/packages/sentencepiece/package.py
    +++ i/var/spack/repos/builtin/packages/sentencepiece/package.py
    @@ -19,10 +19,23 @@ class Sentencepiece(CMakePackage):
     
         license("Apache-2.0")
     
    +    version("0.1.99", sha256="63617eaf56c7a3857597dcd8780461f57dd21381b56a27716ef7d7e02e14ced4")
         version("0.1.91", sha256="acbc7ea12713cd2a8d64892f8d2033c7fd2bb4faecab39452496120ace9a4b1b")
         version("0.1.85", sha256="dd4956287a1b6af3cbdbbd499b7227a859a4e3f41c9882de5e6bdd929e219ae6")
     
    +    variant("with-TCMalloc", default=False, description="Enable TCMalloc if available")
    +    variant("with-TCMalloc-static", default=False, description="Link static library of TCMALLOC")
    +    variant("no-tl", default=False, description="Disable thread_local operator")
    +
         depends_on("cxx", type="build")  # generated
     
         depends_on("cmake@3.1:", type="build")
    -    depends_on("gperftools")  # optional, 10-40% performance improvement
    +    depends_on("gperftools", when="+with-TCMalloc")  # optional, 10-40% performance improvement
    +
    +    def cmake_args(self):
    +        args = [
    +            self.define_from_variant("SPM_ENABLE_TCMALLOC", "with-TCMalloc"),
    +            self.define_from_variant("SPM_TCMALLOC_STATIC", "with-TCMalloc-static"),
    +            self.define_from_variant("SPM_NO_THREADLOCAL", "no-tl"),
    +        ]
    +        return args
    diff --git c/var/spack/repos/builtin/packages/py-psutil/package.py i/var/spack/repos/builtin/packages/py-psutil/package.py
    index 78f0e980..23501f5a 100644
    --- c/var/spack/repos/builtin/packages/py-psutil/package.py
    +++ i/var/spack/repos/builtin/packages/py-psutil/package.py
    @@ -16,6 +16,13 @@ class PyPsutil(PythonPackage):
     
         license("BSD-3-Clause")
     
    +    version("7.0.0", sha256="7be9c3eba38beccb6495ea33afd982a44074b78f28c434a1f51cc07fd315c456")
    +    version("6.1.1", sha256="cf8496728c18f2d0b45198f06895be52f36611711746b7f30c464b422b50e2f5")
    +    version("6.1.0", sha256="353815f59a7f64cdaca1c0307ee13558a0512f6db064e92fe833784f08539c7a")
    +    version("6.0.0", sha256="8faae4f310b6d969fa26ca0545338b21f73c6b15db7c4a8d934a5482faa818f2")
    +    version("5.9.8", sha256="6be126e3225486dff286a8fb9a06246a5253f4c7c53b475ea5f5ac934e64194c")
    +    version("5.9.7", sha256="3f02134e82cfb5d089fddf20bb2e03fd5cd52395321d1c8458a9e58500ff417c")
    +    version("5.9.6", sha256="e4b92ddcd7dd4cdd3f900180ea1e104932c7bce234fb88976e2a3b296441225a")
         version("5.9.5", sha256="5410638e4df39c54d957fc51ce03048acd8e6d60abc0f5107af51e5fb566eb3c")
         version("5.9.4", sha256="3d7f9739eb435d4b1338944abe23f49584bde5395f27487d2ee25ad9a8774a62")
         version("5.9.2", sha256="feb861a10b6c3bb00701063b37e4afc754f8217f0f09c42280586bd6ac712b5c")
    diff --git c/var/spack/repos/builtin/packages/py-wandb/package.py i/var/spack/repos/builtin/packages/py-wandb/package.py
    index 6d094933..7904d486 100644
    --- c/var/spack/repos/builtin/packages/py-wandb/package.py
    +++ i/var/spack/repos/builtin/packages/py-wandb/package.py
    @@ -3,8 +3,12 @@
     #
     # SPDX-License-Identifier: (Apache-2.0 OR MIT)
     
    +import platform
    +import sys
    +
     from spack.package import *
     
    +arch, os = platform.machine(), sys.platform
     
     class PyWandb(PythonPackage):
         """A tool for visualizing and tracking your machine
    @@ -17,22 +21,46 @@ class PyWandb(PythonPackage):
     
         license("MIT")
     
    +    if (arch == "x86_64" or arch == "x64") and os == "linux":
    +        version(
    +            "0.19.9",
    +            sha256="5dc6c7180a5bf1eb5bd9cab8a1886fd980c76d54253c967082fe19d197443a2d",
    +            url="https://files.pythonhosted.org/packages/89/d0/737d26d709bd7bc3f6b2250f41fda3d0787239cfdbd6eb13057c64c81ace/wandb-0.19.9-py3-none-manylinux_2_17_x86_64.manylinux2014_x86_64.whl",
    +            expand=False,
    +        )
    +    elif arch == "aarch64" and os == "linux":
    +        version(
    +            "0.19.9",
    +            sha256="8a074ad070c4e8cbb03b2149a98abbe2d7562220f095a21c736e1abbca399eef",
    +            url="https://files.pythonhosted.org/packages/56/07/47ab3b4f0f4a32d9269ecb60aa71da3e426faa2abe51c4f000778e2696c3/wandb-0.19.9-py3-none-manylinux_2_17_aarch64.manylinux2014_aarch64.whl",
    +            expand=False,
    +        )
    +    version("0.16.6", sha256="86f491e3012d715e0d7d7421a4d6de41abef643b7403046261f962f3e512fe1c")
         version("0.13.9", sha256="0a17365ce1f18306ce7a7f16b943094fac7284bb85f4e52c0685705602f9e307")
     
         depends_on("py-setuptools", type=("build", "run"))
     
    -    depends_on("py-pathtools", type=("build", "run"))
         depends_on("py-setproctitle", type=("build", "run"))
         depends_on("py-appdirs@1.4.3:", type=("build", "run"))
    -    depends_on("py-protobuf@3.19:4", type=("build", "run"))
    +    depends_on("py-protobuf@3.19:", type=("build", "run"))
         conflicts("^py-protobuf@4.21.0")
    +    conflicts("^py-protobuf@5.28.0")
         depends_on("py-typing-extensions", type=("build", "run"), when="^python@:3.9")
     
         depends_on("py-pyyaml", type=("build", "run"))
    -    depends_on("py-click@7:", type=("build", "run"))
    +    depends_on("py-click@7:", type=("build", "run"), when="@0.13")
    +    depends_on("py-click@7.1:", type=("build", "run"), when="@0.15.5:")
         conflicts("^py-click@8.0.0")
         depends_on("py-gitpython@1:", type=("build", "run"))
    +    conflicts("^py-gitpython@3.1.29")
         depends_on("py-requests@2", type=("build", "run"))
         depends_on("py-psutil@5:", type=("build", "run"))
         depends_on("py-sentry-sdk@1.0.0:", type=("build", "run"))
    +    depends_on("py-sentry-sdk@2:", type=("build", "run"), when="@0.19.8:")
         depends_on("py-dockerpy-creds@0.4.0:", type=("build", "run"))
    +    depends_on("py-platformdirs", type=("build", "run"))
    +    depends_on("py-pydantic@2.6:", type=("build", "run"))
    +    depends_on("py-psutil", type=("build", "run"))
    +
    +    # Historical dependencies
    +    depends_on("py-pathtools", type=("build", "run"), when="@:0.15")
