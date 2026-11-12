# Copyright Spack Project Developers. See COPYRIGHT file for details.
#
# SPDX-License-Identifier: (Apache-2.0 OR MIT)

from spack_repo.builtin.build_systems.python import PythonPackage

from spack.package import *


class PyCudaPathfinder(PythonPackage):
    """Utilities for locating CUDA components installed in the user's Python
    environment (cuda.pathfinder, part of NVIDIA cuda-python)."""

    homepage = "https://github.com/NVIDIA/cuda-python"
    git = "https://github.com/NVIDIA/cuda-python"
    url = "https://github.com/NVIDIA/cuda-python/releases/download/cuda-pathfinder-v1.6.0/cuda-python-cuda-pathfinder-v1.6.0.tar.gz"

    license("Apache-2.0")

    # 1.6.0 is the version in NGC pytorch 26.07
    version("1.6.0", sha256="fb863971ad7e53b55333f11066325acddc753bdd9815cbf4b4eb3d49e4ca05ff")

    depends_on("python@3.10:", type=("build", "run"))
    depends_on("py-setuptools@80:", type="build")
    depends_on("py-setuptools-scm@8:", type="build")

    build_directory = "cuda_pathfinder"

    def setup_build_environment(self, env: EnvironmentModifications) -> None:
        # release tarballs carry no git metadata for setuptools_scm
        env.set("SETUPTOOLS_SCM_PRETEND_VERSION", str(self.spec.version))
