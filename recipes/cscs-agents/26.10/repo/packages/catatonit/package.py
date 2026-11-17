# Copyright Spack Project Developers. See COPYRIGHT file for details.
#
# SPDX-License-Identifier: (Apache-2.0 OR MIT)

from spack_repo.builtin.build_systems.autotools import AutotoolsPackage

from spack.package import *


class Catatonit(AutotoolsPackage):
    """A container init so simple it's effectively brain-dead.

    Used by rootless podman as the PID 1 "pause" process that holds the
    container's namespaces open. Built from the actively maintained
    openSUSE fork of the original opencontainers repository.
    """

    homepage = "https://github.com/openSUSE/catatonit"
    url = "https://github.com/openSUSE/catatonit/releases/download/v0.2.1/catatonit.tar.xz"

    license("GPL-2.0-or-later")

    version(
        "0.2.1",
        sha256="9950425501af862e12f618bdc930ea755c46db6a16072a1462b4fc93b2bd59bc",
    )

    depends_on("c", type="build")  # generated

    # The release tarball ships only configure.ac (plus autogen.sh);
    # the configure script must be regenerated at build time.
    depends_on("autoconf", type="build")
    depends_on("automake", type="build")
    depends_on("libtool", type="build")
    depends_on("m4", type="build")

    # Single C file with no external dependencies.
    sanity_check_is_file = ["bin/catatonit"]
