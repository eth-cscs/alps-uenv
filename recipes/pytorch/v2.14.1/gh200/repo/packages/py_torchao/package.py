# Copyright Spack Project Developers. See COPYRIGHT file for details.
#
# SPDX-License-Identifier: (Apache-2.0 OR MIT)

from spack_repo.builtin.build_systems.python import PythonPackage

from spack.package import *


class PyTorchao(PythonPackage):
    """PyTorch native quantization and sparsity for training and inference,
    built with the CUDA/CUTLASS kernels (PyPI only has a CPU-agnostic wheel)."""

    homepage = "https://github.com/pytorch/ao"
    git = "https://github.com/pytorch/ao.git"

    license("BSD-3-Clause")

    # 0.18.0 is the version in NGC pytorch 26.07; third_party/cutlass is a submodule
    version("0.18.0", tag="v0.18.0", submodules=True)

    depends_on("c", type="build")
    depends_on("cxx", type="build")
    depends_on("cuda@12.6:", type=("build", "link", "run"))

    depends_on("python@3.10:", type=("build", "run"))
    with default_args(type="build"):
        depends_on("py-setuptools")
        depends_on("py-wheel")
        depends_on("ninja")
    depends_on("py-torch+cuda@2.10:", type=("build", "link", "run"))

    def setup_build_environment(self, env: EnvironmentModifications) -> None:
        env.set("CUDA_HOME", self.spec["cuda"].prefix)
        # sm_90a enables the Hopper CUTLASS kernels (setup.py checks for compute_90a)
        env.set("TORCH_CUDA_ARCH_LIST", "9.0a")
        # cap: CUTLASS kernels need several GB per nvcc process
        env.set("MAX_JOBS", str(min(make_jobs, 32)))
        # setup.py appends "+git<sha>" otherwise
        env.set("VERSION_SUFFIX", "")
        env.set("USE_CPP", "1")
