# Copyright Spack Project Developers. See COPYRIGHT file for details.
#
# SPDX-License-Identifier: (Apache-2.0 OR MIT)

"""
Custom Spack package for Intel DPC++ (intel/llvm sycl branch) with HIP/ROCm backend.

This builds the full DPC++ SYCL compiler from the intel/llvm repository with
support for AMD GPUs via the HIP backend, targeting gfx90a (MI250X) and
gfx942 (MI300A/MI300X).

The build approach mirrors the upstream configure.py --hip flag:
  - AMDGPU added to LLVM_TARGETS_TO_BUILD
  - hip added to SYCL_ENABLE_BACKENDS
  - lld added to LLVM_ENABLE_PROJECTS (required for AMDGPU linking chain)
  - libclc built as a runtime target via LLVM_RUNTIME_TARGETS / LLVM_ENABLE_RUNTIMES
  - UR_HIP_ROCM_DIR / UR_HIP_* used for Unified Runtime HIP adapter (not HIP_PATH)
  - SYCL_BUILD_UR_HIP_PLATFORM=AMD
"""

import os

from spack_repo.builtin.build_systems.cmake import CMakePackage, generator

from spack.package import *


class Llvmdpcpp(CMakePackage):
    """Intel DPC++ SYCL compiler built from the intel/llvm open-source repository,
    with HIP/ROCm backend for AMD GPUs."""

    homepage = "https://github.com/intel/llvm"
    git = "https://github.com/intel/llvm.git"

    maintainers("gandanie")

    version("sycl", branch="sycl", preferred=True)
    version("sycl-2025.1", tag="sycl/unified/2025.1")

    variant("clang", default=True, description="Build clang (required for DPC++)")
    variant("hip", default=False, description="Enable HIP/ROCm backend for AMD GPUs")

    depends_on("cmake@3.20:", type="build")
    depends_on("ninja", type="build")
    depends_on("python@3.6:", type="build")
    depends_on("zstd", type="link")

    # HIP/ROCm dependencies
    # Unified Runtime HIP adapter needs HIP headers/lib, COMGR headers/lib, and HSA headers.
    # Note: the UR HIP CMakeLists.txt uses a single UR_HIP_INCLUDE_DIR for both
    # hip and amd_comgr headers, and a single UR_HIP_LIB_DIR for both
    # libamdhip64.so and libamd_comgr.so.  In a monolithic /opt/rocm install
    # these all live together, but Spack splits them across separate prefixes.
    # We create a symlink-farm staging directory at build time (see
    # _create_rocm_staging_dirs below) to satisfy the UR adapter checks.
    depends_on("hip", when="+hip")
    depends_on("comgr", when="+hip")
    depends_on("hsa-rocr-dev", when="+hip")
    depends_on("llvm-amdgpu", when="+hip")

    # Force clang on
    conflicts("~clang", msg="DPC++ requires clang")

    generator("ninja")

    def _create_rocm_staging_dirs(self):
        """Create staging include/lib directories merging hip and comgr prefixes.

        The UR HIP adapter (unified-runtime/source/adapters/hip/CMakeLists.txt)
        uses a single UR_HIP_INCLUDE_DIR to look for both HIP headers and the
        amd_comgr.h header, and a single UR_HIP_LIB_DIR for both libamdhip64.so
        and libamd_comgr.so.  In a monolithic ROCm install these share the same
        directory; in Spack they are in separate prefixes.  We create symlink
        farms under the source staging path to satisfy both checks.
        """
        staging = os.path.join(self.stage.source_path, "spack-rocm-staging")
        inc_staging = os.path.join(staging, "include")
        lib_staging = os.path.join(staging, "lib")
        os.makedirs(inc_staging, exist_ok=True)
        os.makedirs(lib_staging, exist_ok=True)

        for pkg_name in ["hip", "comgr"]:
            pkg_spec = self.spec[pkg_name]
            for subdir, staging_dir in [("include", inc_staging), ("lib", lib_staging)]:
                src_dir = os.path.join(pkg_spec.prefix, subdir)
                if os.path.isdir(src_dir):
                    for entry in os.listdir(src_dir):
                        src = os.path.join(src_dir, entry)
                        dst = os.path.join(staging_dir, entry)
                        if not os.path.exists(dst):
                            os.symlink(src, dst)

        return inc_staging, lib_staging

    @property
    def root_cmakelists_dir(self):
        """The CMakeLists.txt is in the llvm subdirectory."""
        return "llvm"

    def cmake_args(self):
        spec = self.spec
        src = self.stage.source_path

        # Paths to DPC++-specific sub-projects within intel/llvm
        sycl_dir = os.path.join(src, "sycl")
        spirv_dir = os.path.join(src, "llvm-spirv")
        xpti_dir = os.path.join(src, "xpti")
        xptifw_dir = os.path.join(src, "xptifw")
        libdevice_dir = os.path.join(src, "libdevice")
        jit_dir = os.path.join(src, "sycl-jit")

        # LLVM targets: X86 host + SPIRV for SYCL IR
        llvm_targets = "X86;SPIRV"

        # SYCL backends (level_zero included for CPU/Intel GPU fallback)
        sycl_backends = ["opencl", "level_zero"]

        # Projects: lld is required for AMDGPU linking chain
        llvm_projects = (
            "clang;llvm-spirv;opencl;xpti;xptifw;libdevice;sycl;sycl-jit"
        )

        # Runtime targets for libclc device library
        # "default" covers non-GPU (CPU, OpenCL) runtimes
        runtime_targets = ["default"]

        if spec.satisfies("+hip"):
            llvm_targets += ";AMDGPU"
            sycl_backends.append("hip")
            # lld is required for AMDGPU ELF code object linking
            llvm_projects += ";lld"
            # libclc AMD target (generic; arch chosen at application compile time)
            runtime_targets.append("amdgcn-amd-amdhsa-llvm")

        args = [
            self.define("CMAKE_BUILD_TYPE", "Release"),
            self.define("LLVM_ENABLE_ASSERTIONS", False),
            self.define("LLVM_TARGETS_TO_BUILD", llvm_targets),
            self.define("LLVM_EXTERNAL_PROJECTS",
                        "sycl;llvm-spirv;opencl;xpti;xptifw;libdevice;sycl-jit"),
            self.define("LLVM_EXTERNAL_SYCL_SOURCE_DIR", sycl_dir),
            self.define("LLVM_EXTERNAL_LLVM_SPIRV_SOURCE_DIR", spirv_dir),
            self.define("LLVM_EXTERNAL_XPTI_SOURCE_DIR", xpti_dir),
            self.define("XPTI_SOURCE_DIR", xpti_dir),
            self.define("LLVM_EXTERNAL_XPTIFW_SOURCE_DIR", xptifw_dir),
            self.define("LLVM_EXTERNAL_LIBDEVICE_SOURCE_DIR", libdevice_dir),
            self.define("LLVM_EXTERNAL_SYCL_JIT_SOURCE_DIR", jit_dir),
            self.define("LLVM_ENABLE_PROJECTS", llvm_projects),
            self.define("LLVM_BUILD_TOOLS", True),
            self.define("LLVM_ENABLE_ZSTD", True),
            self.define("LLVM_USE_STATIC_ZSTD", True),
            self.define("SYCL_ENABLE_WERROR", False),
            self.define("SYCL_INCLUDE_TESTS", False),
            self.define("BUILD_SHARED_LIBS", False),
            self.define("SYCL_ENABLE_XPTI_TRACING", False),
            self.define("SYCL_ENABLE_BACKENDS", ";".join(sycl_backends)),
            self.define("SYCL_ENABLE_EXTENSION_JIT", True),
            self.define("SYCL_ENABLE_MAJOR_RELEASE_PREVIEW_LIB", True),
            self.define("BUG_REPORT_URL", "https://github.com/intel/llvm/issues"),
            # libclc runtime targets (mirrors configure.py libclc_enabled path)
            self.define("LLVM_RUNTIME_TARGETS", ";".join(runtime_targets)),
        ]

        # Use llvm-amdgpu clang/clang++ as the host compiler to build intel/llvm.
        # This avoids the system GCC 7.5 fallback on SLES 15 and is more
        # consistent with a clang-based build environment.
        amdgpu_bin = os.path.join(spec["llvm-amdgpu"].prefix, "bin")
        args.append(self.define("CMAKE_C_COMPILER", os.path.join(amdgpu_bin, "clang")))
        args.append(self.define("CMAKE_CXX_COMPILER", os.path.join(amdgpu_bin, "clang++")))

        # Suppress pragma-once warnings-as-errors from AMD clang headers / third-party
        # headers that use #pragma once (e.g. hipdnn's MiopenLegacyPlugin.hpp).
        # -Wno-error=pragma-once-outside-header turns the promotion to error off
        # while keeping any warning visible; -Wno-pragma-once-outside-header
        # silences it entirely.
        no_pragma_once_err = "-Wno-error=pragma-once-outside-header"
        args.append(self.define("CMAKE_C_FLAGS", no_pragma_once_err))
        args.append(self.define("CMAKE_CXX_FLAGS", no_pragma_once_err))

        # Add per-runtime libclc enablement (configure.py pattern)
        for target in runtime_targets:
            if target != "default":
                args.append(
                    self.define(
                        "RUNTIMES_{}_LLVM_ENABLE_RUNTIMES".format(target),
                        "libclc",
                    )
                )

        if spec.satisfies("+hip"):
            # Create staging dirs that merge hip + comgr headers/libs into a
            # single directory tree, as required by the UR HIP adapter.
            inc_staging, lib_staging = self._create_rocm_staging_dirs()
            hsa_prefix = spec["hsa-rocr-dev"].prefix
            args.extend([
                self.define("SYCL_BUILD_UR_HIP_PLATFORM", "AMD"),
                self.define("UR_HIP_INCLUDE_DIR", inc_staging),
                self.define("UR_HIP_HSA_INCLUDE_DIR",
                            os.path.join(hsa_prefix, "include")),
                self.define("UR_HIP_LIB_DIR", lib_staging),
            ])

        return args
