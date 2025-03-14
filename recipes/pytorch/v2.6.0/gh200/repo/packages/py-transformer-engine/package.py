# Copyright 2013-2024 Lawrence Livermore National Security, LLC and other
# Spack Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: (Apache-2.0 OR MIT)

from spack.package import *


class PyTransformerEngine(PythonPackage, CudaPackage):
    """
    A library for accelerating Transformer models on NVIDIA GPUs, including fp8 precision on Hopper
    GPUs.
    """

    homepage = "https://github.com/NVIDIA/TransformerEngine"
    url = "https://github.com/NVIDIA/TransformerEngine/archive/refs/tags/v0.0.tar.gz"
    git = "https://github.com/NVIDIA/TransformerEngine.git"
    maintainers("aurianer")

    license("Apache-2.0")

    version("1.4", tag="v1.4", submodules=True)
    version("main", branch="main", submodules=True)

    depends_on("cxx", type="build")  # generated

    variant("userbuffers", default=True, description="Enable userbuffers, this option needs MPI.")

    patch("python_v3.13.patch", when="@main")

    with default_args(type=("build")):
        depends_on("py-setuptools")
        depends_on("cmake@3.21:")
        depends_on("ninja")

    with default_args(type=("build", "link")):
        depends_on("py-pybind11")
    
    with default_args(type=("build", "link", "run")):
        depends_on("py-pydantic")
        depends_on("py-importlib-metadata@1:")
        depends_on("py-packaging")
        depends_on("py-torch+cuda+cudnn")
        depends_on("cudnn")
        depends_on("mpi", when="+userbuffers")

    def setup_build_environment(self, env):
        env.set("NVTE_FRAMEWORK", "pytorch")
        env.set("CUDNN_PATH", self.spec["cudnn"].prefix)
        env.set("CUDNN_HOME", self.spec["cudnn"].prefix)
        env.set("CUDNN_ROOT", self.spec["cudnn"].prefix)
        env.prepend_path("CPLUS_INCLUDE_PATH", self.spec["cudnn"].prefix.include)
        if self.spec.satisfies("+userbuffers"):
            env.set("NVTE_WITH_USERBUFFERS", "1")
            env.set("NVTE_UB_WITH_MPI", "1")
            env.set("MPI_HOME", self.spec["mpi"].prefix)
        arch_str = ";".join(self.spec.variants["cuda_arch"].value)
        env.set("CUDAARCHS", arch_str)
