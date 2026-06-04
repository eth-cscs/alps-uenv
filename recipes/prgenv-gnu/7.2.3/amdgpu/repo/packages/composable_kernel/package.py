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

    variant("amdgpu_target", values=("gfx90a","gfx942",), multi=True, default="gfx90a", description="AMD GPU target")
    variant("amdgpu_target_sram_ecc", values=("gfx90a","gfx942",),
            multi=True, default="gfx90a", description="SRAM ECC option")

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

