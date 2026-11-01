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
        args.append(self.define("MIOPEN_REQ_LIBS_ONLY", True))
        args.append(self.define("CK_PARALLEL_COMPILE_JOBS", 24))
        return args
