# Copyright Spack Project Developers. See COPYRIGHT file for details.
#
# SPDX-License-Identifier: (Apache-2.0 OR MIT)

from spack_repo.builtin.packages.composable_kernel.package import (
    ComposableKernel as BuiltinComposableKernel,
)

from spack.package import *


class ComposableKernel(BuiltinComposableKernel):
    def cmake_args(self):
        args = super().cmake_args()
        # Only build the instances MIOpen links (device_conv_operations).
        args.append(self.define("MIOPEN_REQ_LIBS_ONLY", True))
        args.append(self.define("CK_PARALLEL_COMPILE_JOBS", 24))
        # Keep --offload-compress (CK's default). Uncompressed, the fat
        # binaries in libdevice_conv_operations.a push libMIOpen.so past 2 GiB
        # and the link fails with "relocation R_X86_64_PC32 out of range".
        # This relies on llvm-amdgpu being built with zstd (LLVM_ENABLE_ZSTD):
        # its zlib fallback produces bundles that fail to decompress, see
        # https://github.com/ROCm/rocm-libraries/issues/6085
        return args
