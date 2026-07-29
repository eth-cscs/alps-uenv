# Copyright Spack Project Developers. See COPYRIGHT file for details.
#
# SPDX-License-Identifier: (Apache-2.0 OR MIT)

from spack_repo.builtin.build_systems.cmake import CMakePackage

from spack.package import *


class AnariOspray(CMakePackage):
    """FIXME: Put a proper description of your package here."""

    # FIXME: Add a proper url for your package's homepage here.
    homepage = "https://www.example.com"
    url = "https://github.com/ospray/anari-ospray/archive/main.tar.gz"
    git = "https://github.com/ospray/anari-ospray"

    maintainers("albestro")

    license("Apache-2.0", checked_by="albestro")

    version("master")

    depends_on("cxx", type="build")
    depends_on("python@3:", type="build")

    depends_on("anari-sdk@0.13:0.14")
    depends_on("ospray@3.2.0:")

    def cmake_args(self):
        args = []
        return args
