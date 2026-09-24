# Copyright Spack Project Developers. See COPYRIGHT file for details.
#
# SPDX-License-Identifier: (Apache-2.0 OR MIT)

from spack_repo.builtin.build_systems.python import PythonPackage
from spack_repo.builtin.build_systems.cuda import CudaPackage

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

    version("2.19", tag="v2.19", submodules=True)
    version("2.11", tag="v2.11", submodules=True)
    version("2.10", tag="v2.10", submodules=True)
    version("2.9", tag="v2.9", submodules=True)
    version("2.8", tag="v2.8", submodules=True)
    #version("1.4", tag="v1.4", submodules=True)
    version("main", branch="main", submodules=True)

    #variant("userbuffers", default=True, description="Enable userbuffers, this option needs MPI.")

    depends_on("cxx", type="build")  # generated
    depends_on("c", type="build")

    with default_args(type=("build")):
        depends_on("py-setuptools")
        depends_on("cmake@3.21:")
        depends_on("ninja")
        depends_on("nvidia-mathdx")

    with default_args(type=("build", "link")):
        depends_on("py-pybind11")

    with default_args(type=("build", "link", "run")):
        depends_on("py-pydantic")
        depends_on("py-importlib-metadata@1:")
        depends_on("py-packaging")
        depends_on("py-einops")
        depends_on("py-onnx")
        depends_on("py-onnxscript")
        depends_on("py-nvdlfw-inspect", when="@2.12:")
        depends_on("py-nvidia-cudnn-frontend@1.28:", when="@2.18:")
        depends_on("py-torch+cuda+cudnn")
        depends_on("cudnn@9.3:")
        depends_on("nvshmem")
        depends_on("cublasmp@0.8:")
        depends_on("nccl@2.30:")
    
    #depends_on("py-setuptools", type="build")
    #depends_on("cmake@3.18:")
    #depends_on("py-pydantic")
    #depends_on("py-importlib-metadata")

    #with default_args(type=("build", "run")):
    #    depends_on("py-accelerate")
    #    depends_on("py-datasets")
    #    depends_on("py-flash-attn@2.2:2.4.2")
    #    depends_on("py-packaging")
    #    depends_on("py-torchvision")
    #    depends_on("py-transformers")
    #    depends_on("mpi", when="+userbuffers")

 

    #with default_args(type=("build", "link", "run")):
    #    depends_on("py-torch+cuda+cudnn")

    #def setup_build_environment(self, env: EnvironmentModifications) -> None:
    #    env.set("NVTE_FRAMEWORK", "pytorch")
    #    if self.spec.satisfies("+userbuffers"):
    #        env.set("NVTE_WITH_USERBUFFERS", "1")
    #        env.set("MPI_HOME", self.spec["mpi"].prefix)

    def patch(self):
        # Transformer Engine 2.11 is missing this include; newer releases
        # contain it already.
        target = "transformer_engine/common/nvshmem_api/nvshmem_waitkernel.cu"
        cuda_driver_include = '#include "../util/cuda_driver.h"'
        with open(target, "r", encoding="utf-8") as f:
            source = f.read()
        if cuda_driver_include not in source:
            filter_file(
                '#include "../util/logging.h"',
                f'#include "../util/logging.h"\n{cuda_driver_include}',
                target,
                string=True,
            )
        cm = 'transformer_engine/common/nvshmem_api/CMakeLists.txt'
        # Only add once
        with open(cm, 'r', encoding='utf-8') as f:
            txt = f.read()
        inc = 'target_include_directories(nvshmemapi PRIVATE "${CMAKE_CURRENT_SOURCE_DIR}/../include")'
        if inc not in txt:
            with open(cm, 'a', encoding='utf-8') as f:
                f.write('\n' + inc + '\n')

    def setup_build_environment(self, env: EnvironmentModifications) -> None:
        env.set("NVTE_FRAMEWORK", "pytorch")
        cuda = self.spec["cuda"].prefix
        arch_str = ";".join(self.spec.variants["cuda_arch"].value)
        env.set("NVTE_CUDA_ARCHS", arch_str)
        env.set("CUDA_HOME", cuda)
        env.set("CUDA_PATH", cuda)
        # CUDA 13 installs libcudacxx below include/cccl. NVSHMEM's public
        # headers include <cuda/std/...>, including from host C++ sources.
        env.prepend_path("CPATH", join_path(cuda.include, "cccl"))
        env.set("MAX_JOBS", make_jobs)
        env.set("NVTE_BUILD_THREADS_PER_JOB", "4")

        cudnn = self.spec["cudnn"].prefix
        env.set("CUDNN_PATH", cudnn)
        env.prepend_path("CPATH", cudnn.include)
        env.prepend_path("LIBRARY_PATH", cudnn.lib)

        env.set("NVTE_ENABLE_NVSHMEM", "1")
        env.set("NVSHMEM_HOME", self.spec["nvshmem"].prefix)

        cublasmp = self.spec["cublasmp"].prefix 
        env.set("NVTE_WITH_CUBLASMP", "1")
        env.set("CUBLASMP_HOME", cublasmp)
        env.prepend_path("CPATH", cublasmp.include)
        env.prepend_path("LIBRARY_PATH", cublasmp.lib)
        
        mathdx = self.spec["nvidia-mathdx"].prefix
        extra = [
            f"-DMATHDX_INCLUDE_DIR={mathdx.include}",
        ]
        env.set("NVTE_CMAKE_EXTRA_ARGS", " ".join(extra))

        nccl = self.spec["nccl"].prefix
        env.set("NCCL_HOME", nccl)
        env.set("NVTE_WITH_NCCL_EP", "1")
        env.prepend_path("CPATH", nccl.include)        # picked up by gcc/clang/nvcc
        env.prepend_path("LIBRARY_PATH", nccl.lib)     # picked up at link time
