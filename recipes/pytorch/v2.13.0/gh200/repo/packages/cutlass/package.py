# Copyright Spack Project Developers. See COPYRIGHT file for details.
#
# SPDX-License-Identifier: (Apache-2.0 OR MIT)

from spack_repo.builtin.packages.cutlass.package import Cutlass as BuiltinCutlass


class Cutlass(BuiltinCutlass):
    """CUDA Templates for Linear Algebra Subroutines."""

    def cmake_args(self):
        return super().cmake_args() + [self.define("CUTLASS_ENABLE_EXAMPLES", False)]
