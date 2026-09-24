# Copyright Spack Project Developers. See COPYRIGHT file for details.
#
# SPDX-License-Identifier: (Apache-2.0 OR MIT)

from spack_repo.builtin.build_systems.python import PythonPackage

from spack.package import *


class PyCudaCore(PythonPackage):
    """Pythonic access to the CUDA runtime and core functionality."""

    homepage = "https://github.com/NVIDIA/cuda-python"

    version(
        "1.0.1",
        url="https://github.com/NVIDIA/cuda-python/releases/download/v13.3.1/cuda-python-v13.3.1.tar.gz",
        sha256="5d21c94fb373c9dc5c71f922a4356bb0e292b85c1a3c04930a37834f5201a00d",
    )

    depends_on("cuda@13.3.0")
    depends_on("python@3.10:", type=("build", "run"))
    depends_on("py-cython@3.2:3.2", type="build")
    depends_on("py-numpy", type=("build", "run"))
    depends_on("py-cuda-bindings@13.3.1", type=("build", "run"))
    depends_on("py-cuda-pathfinder@1.5:", type=("build", "run"))
    depends_on("py-setuptools@80:", type="build")
    depends_on("py-setuptools-scm@8:", type="build")

    build_directory = "cuda_core"

    def setup_build_environment(self, env):
        env.set("SETUPTOOLS_SCM_PRETEND_VERSION_FOR_CUDA_CORE", str(self.version))
        env.append_path("LIBRARY_PATH", self.spec["cuda"].prefix.lib64)
