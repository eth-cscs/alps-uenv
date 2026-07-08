# Copyright Spack Project Developers. See COPYRIGHT file for details.
#
# SPDX-License-Identifier: (Apache-2.0 OR MIT)

"""
Custom Spack package for Intel DPC++ (intel/llvm sycl branch).

This builds the full DPC++ SYCL compiler from the intel/llvm repository,
replicating what `configure.py --cuda` does but through Spack.
"""

import os

from spack_repo.builtin.build_systems.cmake import CMakePackage, generator
from spack_repo.builtin.build_systems.cuda import CudaPackage

from spack.package import *


class Llvmdpcpp(CMakePackage, CudaPackage):
    """Intel DPC++ SYCL compiler built from the intel/llvm open-source repository."""

    homepage = "https://github.com/intel/llvm"
    git = "https://github.com/intel/llvm.git"

    maintainers("gandanie")

    version("sycl", branch="sycl", preferred=True)
    version("sycl-2025.1", tag="sycl/unified/2025.1")

    variant("clang", default=True, description="Build clang (required for DPC++)")

    depends_on("cmake@3.20:", type="build")
    depends_on("ninja", type="build")
    depends_on("python@3.6:", type="build")
    depends_on("zstd", type="link")

    # CUDA dependencies
    depends_on("cuda@12:", when="+cuda")

    # Force clang on
    conflicts("~clang", msg="DPC++ requires clang")

    generator("ninja")

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

        # LLVM targets
        llvm_targets = "AArch64;ARM;X86;SPIRV"

        # SYCL backends
        sycl_backends = ["opencl", "level_zero"]

        # LibCLC targets
        libclc_targets = ""

        if spec.satisfies("+cuda"):
            llvm_targets += ";NVPTX"
            sycl_backends.append("cuda")
            libclc_targets = "nvptx64-nvidia-cuda"

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
            self.define("LLVM_ENABLE_PROJECTS",
                        "clang;llvm-spirv;opencl;xpti;xptifw;"
                        "libdevice;sycl;sycl-jit;libclc"),
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
        ]

        if spec.satisfies("+cuda"):
            args.extend([
                self.define("CUDA_TOOLKIT_ROOT_DIR", spec["cuda"].prefix),
                self.define("LIBCLC_TARGETS_TO_BUILD", libclc_targets),
                self.define("LIBCLC_GENERATE_REMANGLED_VARIANTS", True),
            ])

        return args
