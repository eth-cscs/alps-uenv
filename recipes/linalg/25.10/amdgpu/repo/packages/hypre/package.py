# Copyright Spack Project Developers. See COPYRIGHT file for details.
#
# SPDX-License-Identifier: (Apache-2.0 OR MIT)

from spack_repo.builtin.packages.hypre.package import Hypre as BuiltinHypre


class Hypre(BuiltinHypre):
    def configure_args(self):
        args = super().configure_args()
        if not self.spec.satisfies("@2.33.0 +rocm"):
            return args

        result = []
        for arg in args:
            if arg.startswith("--with-extra-CUFLAGS="):
                # Hypre 2.33's HIP configure path defaults to C++14. Extra flags come last.
                arg += " -std=c++17 -DHIP_DISABLE_WARP_SYNC_BUILTINS"
                if self.spec.satisfies("+superlu-dist ^hipblas@6.3:"):
                    arg += " -I" + str(self.spec["hipblas-common"].prefix.include)
            elif arg.startswith("--with-gpu-arch="):
                # The builtin recipe keeps only one target; this image serves both AMD GPUs.
                targets = sorted(self.spec.variants["amdgpu_target"].value)
                arg = "--with-gpu-arch=" + " ".join(targets)
            result.append(arg)
        return result
