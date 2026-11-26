# Copyright Spack Project Developers. See COPYRIGHT file for details.
#
# SPDX-License-Identifier: (Apache-2.0 OR MIT)

from spack_repo.builtin.build_systems.python import PythonPackage

from spack.package import *


class PyNvidiaResiliencyExt(PythonPackage):
    """NVIDIA Resiliency Extension: fault tolerance, in-process restart,
    straggler detection (CUPTI extension) and checkpointing for PyTorch."""

    homepage = "https://github.com/NVIDIA/nvidia-resiliency-ext"
    url = "https://github.com/NVIDIA/nvidia-resiliency-ext/archive/refs/tags/v0.6.0.tar.gz"
    git = "https://github.com/NVIDIA/nvidia-resiliency-ext.git"

    license("Apache-2.0")

    # 0.6.0 is the version in NGC pytorch 26.07 (PyPI only has binary wheels).
    # Release tarball rather than tag="v0.6.0": the git checkout failed inside the build
    # sandbox (status 128) although it works outside; the repo has no submodules.
    version("0.6.0", sha256="66d4a962521883508cf737056a7f4db60adc8b6603dddcfd9a55d056f8b8d424")

    depends_on("cxx", type="build")
    depends_on("cuda")

    depends_on("python@3.10:", type=("build", "run"))
    with default_args(type="build"):
        depends_on("py-poetry-core@1:")
        depends_on("py-poetry-dynamic-versioning@1:")
        depends_on("py-setuptools")
        depends_on("py-wheel")
        depends_on("py-pybind11")
        # pyproject pins grpcio-tools 1.76.x to generate the _pb2 modules; spack has
        # no 1.76, and the generated code only has to match the runtime grpcio below
        depends_on("py-grpcio-tools@1.76:")
    with default_args(type=("build", "run")):
        depends_on("py-torch@2.3:")
        depends_on("py-packaging")
        depends_on("py-psutil@6:")
        depends_on("py-pyyaml")
        depends_on("py-numpy@1.26:")
        depends_on("py-nvidia-ml-py@12.570.86:")
        depends_on("py-defusedxml")
        depends_on("py-httpx@0.24:")
        depends_on("py-grpcio@1.76:1")
        depends_on("py-grpcio-tools@1.76:1")
        depends_on("py-protobuf@4.22:")

    def setup_build_environment(self, env: EnvironmentModifications) -> None:
        # build.py locates cupti.h / libcupti.so under CUDA_PATH
        env.set("CUDA_PATH", self.spec["cuda"].prefix)
        # poetry-dynamic-versioning derives the version from git otherwise
        env.set("POETRY_DYNAMIC_VERSIONING_BYPASS", str(self.spec.version))
