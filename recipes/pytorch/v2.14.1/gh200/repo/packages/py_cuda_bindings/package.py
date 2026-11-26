# Copyright Spack Project Developers. See COPYRIGHT file for details.
#
# SPDX-License-Identifier: (Apache-2.0 OR MIT)

from spack_repo.builtin.build_systems.python import PythonPackage

from spack.package import *


class PyCudaBindings(PythonPackage):
    """Low-level Cython bindings and Python wrappers for the CUDA driver and
    runtime APIs (cuda.bindings, part of NVIDIA cuda-python)."""

    homepage = "https://github.com/NVIDIA/cuda-python"
    git = "https://github.com/NVIDIA/cuda-python"
    url = "https://github.com/NVIDIA/cuda-python/releases/download/v13.3.1/cuda-python-v13.3.1.tar.gz"

    license("LicenseRef-NVIDIA-SOFTWARE-LICENSE")

    # 13.3.1 is the version in NGC pytorch 26.07
    version("13.3.1", sha256="5d21c94fb373c9dc5c71f922a4356bb0e292b85c1a3c04930a37834f5201a00d")
    version("13.0.2", sha256="984197c834016a31f0da6f7052efbf191105e593ff469ff24bbf801a7de47cba")

    # bindings are generated for a specific CUDA minor release
    depends_on("cuda@13.3", when="@13.3")
    depends_on("cuda@13.0.2", when="@13.0.2")

    depends_on("python@3.10:", type=("build", "run"))
    depends_on("py-cython@3.2:3.2", when="@13.3:", type="build")
    depends_on("py-cython", type="build")
    depends_on("py-pyclibrary@0.1.7:", type="build")
    depends_on("py-setuptools@80:", when="@13.3:", type="build")
    depends_on("py-setuptools", type="build")
    depends_on("py-setuptools-scm@8:", when="@13.3:", type="build")
    depends_on("py-cuda-pathfinder@1.4.2:", when="@13.3:", type=("build", "run"))

    build_directory = "cuda_bindings"

    def setup_build_environment(self, env: EnvironmentModifications) -> None:
        env.set("CUDA_HOME", self.spec["cuda"].prefix)
        env.set("CUDA_PATH", self.spec["cuda"].prefix)
        env.append_path("LIBRARY_PATH", self.spec["cuda"].prefix.lib64)
        env.set("CUDA_PYTHON_PARALLEL_LEVEL", str(make_jobs))
        # release tarballs carry no git metadata for setuptools_scm
        env.set("SETUPTOOLS_SCM_PRETEND_VERSION", str(self.spec.version))
