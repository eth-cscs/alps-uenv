# Copyright Spack Project Developers. See COPYRIGHT file for details.
#
# SPDX-License-Identifier: (Apache-2.0 OR MIT)

from spack.package import depends_on, which
from spack_repo.builtin.packages.libcxi.package import Libcxi as BuiltinLibcxi


class Libcxi(BuiltinLibcxi):
    # The pinned release branch is a Git checkout too; @main guards miss its bootstrap tools.
    depends_on("autoconf", type="build")
    depends_on("automake", type="build")
    depends_on("libtool", type="build")
    depends_on("pkgconfig", type="build")

    def autoreconf(self, spec, prefix):
        which("sh")("autogen.sh")
