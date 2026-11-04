# Copyright Spack Project Developers. See COPYRIGHT file for details.
#
# SPDX-License-Identifier: (Apache-2.0 OR MIT)

from spack_repo.builtin.build_systems.python import PythonPackage

from spack.package import *


class PyCudaPython(PythonPackage):
    """CUDA Python metapackage: cuda.bindings, cuda.core and cuda.pathfinder."""

    homepage = "https://github.com/NVIDIA/cuda-python"
    git = "https://github.com/NVIDIA/cuda-python"
    url = "https://github.com/NVIDIA/cuda-python/releases/download/v13.3.1/cuda-python-v13.3.1.tar.gz"

    license("LicenseRef-NVIDIA-SOFTWARE-LICENSE")

    # 13.3.1 is the version in NGC pytorch 26.07
    version("13.3.1", sha256="5d21c94fb373c9dc5c71f922a4356bb0e292b85c1a3c04930a37834f5201a00d")

    depends_on("python@3.10:", type=("build", "run"))
    depends_on("py-setuptools@80:", type="build")
    depends_on("py-setuptools-scm@8:", type="build")

    # install_requires of cuda-python 13.3.1
    with default_args(type=("build", "run")):
        depends_on("py-cuda-bindings@13.3.1", when="@13.3.1")
        depends_on("py-cuda-core@1.0", when="@13.3.1")
        depends_on("py-cuda-pathfinder@1.1:1", when="@13.3.1")

    build_directory = "cuda_python"

    def setup_build_environment(self, env: EnvironmentModifications) -> None:
        # release tarballs carry no git metadata for setuptools_scm
        env.set("SETUPTOOLS_SCM_PRETEND_VERSION", str(self.spec.version))
