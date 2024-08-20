# Copyright 2013-2024 Lawrence Livermore National Security, LLC and other
# Spack Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: (Apache-2.0 OR MIT)

# ----------------------------------------------------------------------------
# If you submit this package back to Spack as a pull request,
# please first remove this boilerplate and all FIXME comments.
#
# This is a template package file for Spack.  We've put "FIXME"
# next to all the things you'll want to change. Once you've handled
# them, you can save this file and test your package like this:
#
#     spack install libvterm
#
# You can edit this file again by typing:
#
#     spack edit libvterm
#
# See the Spack documentation for more information on packaging.
# ----------------------------------------------------------------------------

from spack.package import *


class Libvterm(MesonPackage):
    """a fork of libvterm that uses meson to improve reliability of package building"""

    homepage = "https://www.example.com"
    url = "https://github.com/bcumming/libvterm/archive/refs/tags/v0.3.3-rc1.tar.gz"

    maintainers("bcumming")

    license("MIT")

    version("0.3.3-rc1", sha256="772bcee8ecc44f91d51285e40ba073f73289d92e50b0ec51573892513e73d354")

    depends_on("meson", type="build")
    depends_on("ninja", type="build")

