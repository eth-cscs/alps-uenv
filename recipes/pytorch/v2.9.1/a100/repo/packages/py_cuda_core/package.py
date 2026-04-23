# Copyright Spack Project Developers. See COPYRIGHT file for details.
#
# SPDX-License-Identifier: (Apache-2.0 OR MIT)

from spack_repo.builtin.build_systems.python import PythonPackage

from spack.package import *


class PyCudaCore(PythonPackage):
    """Pythonic access to NVIDIA's CUDA Runtime and other core functionalities"""

    homepage = "https://github.com/NVIDIA/cuda-python"
    git = "https://github.com/NVIDIA/cuda-python"
    url = "https://github.com/NVIDIA/cuda-python/releases/download/cuda-core-v0.4.2/cuda-python-cuda-core-v0.4.2.tar.gz"

    version("0.5.0", sha256="c2b68fe7c5557a33d275f4516d781738566f90f9b6caab43844401033e21b670")
    version("0.4.2", sha256="4862f0a44534a0049088458f8930f7387687dbdab9e2e7ea95dc668b98f2ac72")
    version("0.4.0", sha256="47a6181f1a8fa1db2df31251c0bb654558b3eddf47c41964bfa39965a46c7b41")
    version("0.2.0", sha256="380d33e26e808d796a600b557e5b7de6bd6677776e9a6736372f14ff80e6b664")

    depends_on("cuda@12:")
    depends_on("python@3.10:", type=("build", "run"))
    depends_on("py-cython", type="build")
    depends_on("py-pyclibrary", type=("build", "run"))
    depends_on("py-pywin32", when="platform=windows", type=("build", "run"))
    depends_on("py-setuptools", type="build")
    depends_on("py-setuptools@77.0.0:", type="build")
    depends_on("py-cuda-bindings", type=("build", "run"))

    build_directory = "cuda_core"

    def setup_build_environment(self, env):
        cuda_version = self.spec["cuda"].version
        if cuda_version >= Version("12.9"):
            env.append_path("LIBRARY_PATH", self.spec["cuda"].prefix.lib64)
