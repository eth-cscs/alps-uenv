# Copyright Spack Project Developers. See COPYRIGHT file for details.
#
# SPDX-License-Identifier: (Apache-2.0 OR MIT)

from spack_repo.builtin.build_systems.python import PythonPackage
from spack_repo.builtin.build_systems import python as pybs

from spack.package import *
import os

class PyTriton(PythonPackage):
    """A language and compiler for custom Deep Learning operations."""

    homepage = "https://github.com/triton-lang/triton"
    url      = "https://github.com/triton-lang/triton/archive/refs/tags/v2.1.0.tar.gz"
    git      = "https://github.com/triton-lang/triton.git"

    license("MIT")

    # Exact Triton and LLVM revisions pinned by PyTorch 2.13.0.
    version("3.7.1", commit="5d6048aa0a324e090ada215b609ea76620133845")
    resource(
        name="llvm",
        git="https://github.com/llvm/llvm-project.git",
        commit="ac5dc54d509169d387fcfd495d71853d81c46484",
        placement="llvm-project",
        when="@3.7.1",
    )

    variant("build-custom-llvm", default=False, description="Build and use an in-prefix llvm-project for Triton")

    depends_on("c",   type="build")
    depends_on("cxx", type="build")

    # Build-time requirements
    with default_args(type="build"):
        depends_on("cmake@3.18:3")
        depends_on("ninja@1.11.1:")
        depends_on("py-setuptools@40.8.0:")
        depends_on("py-pybind11@2.13.1:")
        depends_on("py-lit")
        depends_on("nlohmann-json")

    # Runtime/additional deps
    depends_on("py-setuptools@40.8.0:", type="run", when="@3.2.0")
    depends_on("py-filelock", type=("build", "run"))
    depends_on("zlib-api", type="link")
    conflicts("^openssl@3.3.0")
    depends_on("cuda")

    def setup_run_environment(self, env):
        cuda = self.spec["cuda"].prefix
        cuda_bin = os.path.join(str(cuda), "bin")
        cuda_inc = os.path.join(str(cuda), "include")
        cupti_path = self.spec["cuda"].prefix.extras.CUPTI

        env.set("TRITON_PTXAS_PATH",         os.path.join(cuda_bin, "ptxas"))
        env.set("TRITON_CUOBJDUMP_PATH",     os.path.join(cuda_bin, "cuobjdump"))
        env.set("TRITON_NVDISASM_PATH",      os.path.join(cuda_bin, "nvdisasm"))
        env.set("TRITON_CUDACRT_PATH",       cuda_inc)
        env.set("TRITON_CUDART_PATH",        cuda_inc)
        env.set("TRITON_CUPTI_INCLUDE_PATH", os.path.join(cupti_path, "include"))
        env.set("TRITON_CUPTI_LIB_PATH",     os.path.join(cupti_path, "lib64"))


class PythonPipBuilder(pybs.PythonPipBuilder):

    def _build_llvm(self, pkg: PythonPackage):
        repo_root = pkg.stage.source_path
        llvm_project_path = os.environ.get(
            "LLVM_PROJECT_PATH", os.path.join(repo_root, "llvm-project")
        )
        if not os.path.isdir(os.path.join(llvm_project_path, "llvm")):
            raise InstallError(
                "The staged llvm-project resource is missing. "
                f"Expected {llvm_project_path}/llvm."
            )

        llvm_build_path = os.environ.get(
            "LLVM_BUILD_PATH", os.path.join(llvm_project_path, "build")
        )
        llvm_install_path = os.environ.get(
            "LLVM_INSTALL_PATH", os.path.join(str(pkg.prefix), "triton-llvm")
        )
        llvm_targets = os.environ.get("LLVM_TARGETS", "Native;NVPTX;AMDGPU")
        llvm_projects = os.environ.get("LLVM_PROJECTS", "mlir;llvm;lld")
        llvm_btype = os.environ.get("LLVM_BUILD_TYPE", "Release")

        cmake, ninja = which("cmake"), which("ninja")
        mkdirp(llvm_build_path)
        mkdirp(llvm_install_path)

        cmake(
            "-G",
            "Ninja",
            f"-DCMAKE_BUILD_TYPE={llvm_btype}",
            "-DCMAKE_BUILD_WITH_INSTALL_RPATH=ON",
            "-DLLVM_CCACHE_BUILD=OFF",
            "-DLLVM_ENABLE_ASSERTIONS=ON",
            "-DLLVM_BUILD_TOOLS=ON",
            "-DLLVM_INSTALL_TOOLS=ON",
            "-DLLVM_INSTALL_UTILS=ON",
            "-DLLVM_OPTIMIZED_TABLEGEN=ON",
            f"-DLLVM_TARGETS_TO_BUILD={llvm_targets}",
            "-DCMAKE_EXPORT_COMPILE_COMMANDS=1",
            f"-DLLVM_ENABLE_PROJECTS={llvm_projects}",
            f"-DCMAKE_INSTALL_PREFIX={llvm_install_path}",
            "-B",
            llvm_build_path,
            os.path.join(llvm_project_path, "llvm"),
        )
        ninja("-C", llvm_build_path, f"-j{make_jobs}")
        ninja("-C", llvm_build_path, "install", f"-j{make_jobs}")

        libdir = os.path.join(llvm_install_path, "lib")
        if not os.path.isdir(libdir):
            libdir = os.path.join(llvm_install_path, "lib64")

        return llvm_install_path, os.path.join(llvm_install_path, "include"), libdir
