# Copyright 2013-2023 Lawrence Livermore National Security, LLC and other
# Spack Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: (Apache-2.0 OR MIT)

# import os
import platform

from spack_repo.builtin.build_systems.generic import Package

# import spack.compilers
from spack.package import *

_versions = {
    "7.2.3": {
        "Linux-x86_64": "f8300821a713ea55bc0d8a9116d5733fc50a0641f39c0301fd5415940d9b3d56"
    }
}

class ComposableKernel(Package):
    """Install composable-kernel as a binary package"""

    homepage = "https://github.com/ROCm/composable_kernel"
    url = "file:///capstor/scratch/cscs/simonpi/binary-packages/composable-kernel-7.2.3-1-x86_64.pkg.tar.gz"
    maintainers = ["simonpintarelli"]

    amdgpu_targets = (
        "gfx701",
        "gfx801",
        "gfx802",
        "gfx803",
        "gfx900",
        "gfx900:xnack-",
        "gfx902",
        "gfx904",
        "gfx906",
        "gfx906:xnack-",
        "gfx908",
        "gfx908:xnack-",
        "gfx909",
        "gfx90a",
        "gfx90a:xnack-",
        "gfx90a:xnack+",
        "gfx90c",
        "gfx940",
        "gfx941",
        "gfx942",
        "gfx950",
        "gfx1010",
        "gfx1011",
        "gfx1012",
        "gfx1013",
        "gfx1030",
        "gfx1031",
        "gfx1032",
        "gfx1033",
        "gfx1034",
        "gfx1035",
        "gfx1036",
        "gfx1100",
        "gfx1101",
        "gfx1102",
        "gfx1103",
        "gfx1150",
        "gfx1151",
        "gfx1152",
        "gfx1153",
        "gfx1200",
        "gfx1201",
        "gfx1250",
        "gfx1251",
    )
    variant(
        "amdgpu_target",
        description="AMD GPU architecture",
        values=auto_or_any_combination_of(*amdgpu_targets),
        sticky=True,
    )

    for ver, packages in _versions.items():
        key = "{0}-{1}".format(platform.system(), platform.machine())
        sha = packages.get(key)
        if sha:
            version(
                ver,
                sha256=sha,
                # url=f"https://jfrog.svc.cscs.ch/artifactory/cray-mpich/cray-mpich-{ver}.{platform.machine()}.tar.gz",
                url="file:///capstor/scratch/cscs/simonpi/binary-packages/composable-kernel-7.2.3-1-x86_64.pkg.tar.gz"
            )

    # Need access to compilers to fix compiler paths.
    for ver in [
        "7.2.3",
    ]:
        depends_on("hip+rocm@" + ver, when="@" + ver)
        depends_on("llvm-amdgpu@" + ver, when="@" + ver)

    def install(self, spec, prefix):
        install_tree("opt/rocm", prefix)

