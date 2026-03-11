# Copyright Spack Project Developers. See COPYRIGHT file for details.
#
# SPDX-License-Identifier: (Apache-2.0 OR MIT)

from spack_repo.builtin.build_systems.python import PythonPackage

from spack.package import *


class PyCudaPathfinder(PythonPackage):
    """cuda.pathfinder aims to be a one-stop solution for locating CUDA components."""

    homepage = "https://github.com/NVIDIA/cuda-python"
    git = "https://github.com/NVIDIA/cuda-python"
    url = "https://github.com/NVIDIA/cuda-python/releases/download/cuda-pathfinder-v1.3.3/cuda-python-cuda-pathfinder-v1.3.3.tar.gz"

    version("1.3.3", sha256="974a06b31bdd594f68f750f713994f31ae0b8b8425434563bdc245187f4815e9")
    version("1.2.3", sha256="366e5852499cedfc4a469631a9ca332ef59d5a29d9aafdeda5a78265f314b1d0")

    depends_on("cuda@12:")
    depends_on("python@3.9:", when="@1.2.3:", type=("build", "run"))
    depends_on("python@3.10:", when="@1.3.3:", type=("build", "run"))

    depends_on("py-wheel", type="build")
    depends_on("py-setuptools@64:", when="@1.2.3:", type="build")
    depends_on("py-setuptools@80.0.0:", when="@1.3.3:", type="build")
    depends_on("py-setuptools-scm@8:", when="@1.3.3:", type="build")

    build_directory = "cuda_pathfinder"

    def setup_build_environment(self, env):
        cuda_version = self.spec["cuda"].version
        if cuda_version >= Version("12.9"):
            env.append_path("LIBRARY_PATH", self.spec["cuda"].prefix.lib64)
