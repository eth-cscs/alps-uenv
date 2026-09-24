# Copyright Spack Project Developers. See COPYRIGHT file for details.
#
# SPDX-License-Identifier: (Apache-2.0 OR MIT)

from spack_repo.builtin.build_systems.cuda import CudaPackage
from spack_repo.builtin.build_systems.generic import Package

from spack.package import *


class Cublasmp(Package, CudaPackage):
    """NVIDIA cuBLASMp distributed dense linear algebra library."""

    homepage = "https://docs.nvidia.com/cuda/cublasmp/"

    license("UNKNOWN")

    version(
        "0.8.0.2023",
        sha256="8fecd957f41d4b10b5d85a1203950a8fe560dd8811d677f4130efb3e88d6210b",
        url="https://developer.download.nvidia.com/compute/cublasmp/redist/libcublasmp/linux-sbsa/libcublasmp-linux-sbsa-0.8.0.2023_cuda13-archive.tar.xz",
    )

    conflicts("~cuda", msg="cuBLASMp requires CUDA")

    depends_on("cuda@13:")
    depends_on("nvshmem@3.1:")
    depends_on("nccl@2.30:")

    for cuda_arch in CudaPackage.cuda_arch_values:
        with when(f"cuda_arch={cuda_arch}"):
            depends_on(f"nvshmem cuda_arch={cuda_arch}")
            depends_on(f"nccl cuda_arch={cuda_arch}")

    def install(self, spec, prefix):
        install_tree(".", prefix)
