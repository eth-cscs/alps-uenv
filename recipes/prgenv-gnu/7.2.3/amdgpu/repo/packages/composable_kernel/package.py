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
        # Do not compress the offload bundles (--offload-compress), same as
        # 0010-disable-tensile-co-compression.patch in rocblas. See
        # https://github.com/eth-cscs/alps-uenv/issues/387
        args.append(self.define("DISABLE_OFFLOAD_COMPRESS", True))
        return args
