# Copyright Spack Project Developers. See COPYRIGHT file for details.
#
# SPDX-License-Identifier: (Apache-2.0 OR MIT)

from spack_repo.builtin.packages.rocprofiler_compute.package import (
    RocprofilerCompute as BuiltinRocprofilerCompute,
)

from spack.package import *


class RocprofilerCompute(BuiltinRocprofilerCompute):
    def setup_build_environment(self, env: EnvironmentModifications) -> None:
        super().setup_build_environment(env)
        env.set("ROCM_PATH", self.spec["rocprofiler-sdk"].prefix)
