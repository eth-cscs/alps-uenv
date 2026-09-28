# Copyright Spack Project Developers. See COPYRIGHT file for details.
#
# SPDX-License-Identifier: (Apache-2.0 OR MIT)

from spack_repo.builtin.build_systems.python import PythonPackage

from spack.package import *


class PyCudaPython(PythonPackage):
    """CUDA Python is the home for accessing NVIDIA’s CUDA platform from Python."""

    homepage = "https://github.com/NVIDIA/cuda-python"
    git = "https://github.com/NVIDIA/cuda-python"
    url = "https://github.com/NVIDIA/cuda-python/releases/download/v12.9.0/cuda-python-v12.9.0.tar.gz"

    version("13.0.2", sha256="984197c834016a31f0da6f7052efbf191105e593ff469ff24bbf801a7de47cba")
    version("13.0.1", sha256="7dda5ada869e6e4e35d00120d10f3c7e8fa1600a0324308c68c3d9e0526b0809")
    version("13.0.0", sha256="4df6fb7b465ef668d2899337551f4d0ac7ac06e0fd8c80cb56f61d258afd3a3e")
    version("12.9.1", sha256="9c6c2da8ed59851acbb261b5fac80885d9dd2396a8bea0eba67908b811d7bb50")

    depends_on("cuda@13.0.2", when="@13.0.2")
    depends_on("cuda@13.0.1", when="@13.0.1")
    depends_on("cuda@13.0.0", when="@13.0.0")
    depends_on("cuda@12.9.1", when="@12.9.1")

    depends_on("python@3.9:", type=("build", "run"))
    depends_on("py-cython", type="build")
    depends_on("py-pyclibrary", type=("build", "run"))
    depends_on("py-pywin32", when="platform=windows", type=("build", "run"))
    depends_on("py-setuptools", type="build")
    depends_on("py-setuptools@77.0.0:", when="@12.9.0", type="build")

    build_directory = "cuda_python"

    def setup_build_environment(self, env):
        cuda_version = self.spec["cuda"].version
        if cuda_version >= Version("12.9"):
            env.append_path("LIBRARY_PATH", self.spec["cuda"].prefix.lib64)
