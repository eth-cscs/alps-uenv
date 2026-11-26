# Copyright Spack Project Developers. See COPYRIGHT file for details.
#
# SPDX-License-Identifier: (Apache-2.0 OR MIT)

from spack_repo.builtin.build_systems.python import PythonPackage

from spack.package import *


class PyNvidiaModelopt(PythonPackage):
    """NVIDIA Model Optimizer: quantization, pruning, distillation and
    sparsity for PyTorch models. Installed from the pure-python wheel."""

    homepage = "https://github.com/NVIDIA/Model-Optimizer"
    url = "https://files.pythonhosted.org/packages/83/ab/7e12dd238638624cb9d48904e9205abe16a5b26bdd5f9b91e3357821cf90/nvidia_modelopt-0.44.0-py3-none-any.whl"

    license("Apache-2.0")

    # 0.44.0 is the version in NGC pytorch 26.07
    version(
        "0.44.0",
        sha256="9b54a853dfda161db97a0dfce4d7c24269d1d19966b5e2026094186af897f74d",
        expand=False,
    )

    depends_on("python@3.10:3.14", type=("build", "run"))
    with default_args(type=("build", "run")):
        # the pip "ninja" requirement is only used to JIT-compile extensions
        depends_on("ninja")
        depends_on("py-numpy")
        depends_on("py-nvidia-ml-py@12:")
        depends_on("py-packaging")
        depends_on("py-setuptools@80:")
        depends_on("py-torch@2.8:")
        depends_on("py-tqdm")
        depends_on("py-pyyaml@6:")
        depends_on("py-omegaconf@2.3:")
        depends_on("py-pulp@:3")
        depends_on("py-pydantic@2:")
        depends_on("py-regex")
        depends_on("py-rich")
        depends_on("py-safetensors")
        depends_on("py-scipy")
