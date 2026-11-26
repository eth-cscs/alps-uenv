# Copyright Spack Project Developers. See COPYRIGHT file for details.
#
# SPDX-License-Identifier: (Apache-2.0 OR MIT)

from spack_repo.builtin.build_systems.python import PythonPackage

from spack.package import *


class PyCudaCore(PythonPackage):
    """Pythonic access to NVIDIA's CUDA Runtime and other core functionality
    (cuda.core, part of NVIDIA cuda-python)."""

    homepage = "https://github.com/NVIDIA/cuda-python"
    git = "https://github.com/NVIDIA/cuda-python"
    url = "https://github.com/NVIDIA/cuda-python/releases/download/cuda-core-v1.0.1/cuda-python-cuda-core-v1.0.1.tar.gz"

    license("Apache-2.0")

    # 1.0.1 is the version in NGC pytorch 26.07
    version("1.0.1", sha256="6f4ff33299705f9190c53f1393a3bd1894bcc7ad656d09dd55ddfe7959efb287")
    version("0.5.0", sha256="c2b68fe7c5557a33d275f4516d781738566f90f9b6caab43844401033e21b670")

    depends_on("cuda@12:")
    depends_on("python@3.10:", type=("build", "run"))
    depends_on("py-cython@3.2:3.2", when="@1:", type="build")
    depends_on("py-cython", type="build")
    depends_on("py-setuptools@80:", when="@1:", type="build")
    depends_on("py-setuptools@77:", type="build")
    depends_on("py-setuptools-scm@8:", when="@1:", type="build")
    depends_on("py-numpy", when="@1:", type=("build", "run"))
    depends_on("py-cuda-pathfinder@1.5:", when="@1:", type=("build", "run"))
    depends_on("py-cuda-bindings", type=("build", "run"))

    build_directory = "cuda_core"

    def setup_build_environment(self, env: EnvironmentModifications) -> None:
        env.set("CUDA_HOME", self.spec["cuda"].prefix)
        env.set("CUDA_PATH", self.spec["cuda"].prefix)
        env.append_path("LIBRARY_PATH", self.spec["cuda"].prefix.lib64)
        # release tarballs carry no git metadata for setuptools_scm
        env.set("SETUPTOOLS_SCM_PRETEND_VERSION", str(self.spec.version))
