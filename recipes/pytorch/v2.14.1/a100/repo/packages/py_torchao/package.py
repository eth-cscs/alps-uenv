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

    def patch(self):
        # alps: setup.py builds _C_cutlass_90a (sm_90a) and _C_mxfp8 (sm_100) whenever CUDA
        # is new enough, ignoring TORCH_CUDA_ARCH_LIST; build them only for matching archs.
        # (0.18 has no other CUDA kernels, so for e.g. cuda_arch=80 no CUDA extension is built.)
        archs = self.spec["py-torch"].variants["cuda_arch"].value
        sm90a = "90a" in archs
        sm100 = any(a.startswith("100") for a in archs)
        filter_file(
            "return build_sm90a, build_sm100a",
            f"return build_sm90a and {sm90a}, build_sm100a and {sm100}  # alps",
            "setup.py",
            string=True,
        )

    def setup_build_environment(self, env: EnvironmentModifications) -> None:
        env.set("CUDA_HOME", self.spec["cuda"].prefix)
        # build for torch's cuda_arch: e.g. 90a -> "9.0a" (sm_90a enables the Hopper CUTLASS
        # kernels; setup.py checks for compute_90a), 80 -> "8.0"
        archs = self.spec["py-torch"].variants["cuda_arch"].value
        env.set("TORCH_CUDA_ARCH_LIST", ";".join(f"{a[:-1]}.{a[-1:]}" if not a[-1].isalpha()
                                                 else f"{a[:-2]}.{a[-2:]}" for a in archs))
        # cap: CUTLASS kernels need several GB per nvcc process
        env.set("MAX_JOBS", str(min(make_jobs, 32)))
        # setup.py appends "+git<sha>" otherwise
        env.set("VERSION_SUFFIX", "")
        env.set("USE_CPP", "1")
