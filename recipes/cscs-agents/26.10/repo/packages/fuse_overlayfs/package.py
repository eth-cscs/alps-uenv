# Copyright Spack Project Developers. See COPYRIGHT file for details.
#
# SPDX-License-Identifier: (Apache-2.0 OR MIT)

from spack_repo.builtin.build_systems.autotools import AutotoolsPackage

from spack.package import *


class FuseOverlayfs(AutotoolsPackage):
    """FUSE implementation of overlayfs for rootless containers.

    Podman's storage driver mount program when the kernel's native overlay
    cannot be used (for example, when the caller cannot remount mounts
    private inside a restricted sandbox).
    """

    homepage = "https://github.com/containers/fuse-overlayfs"
    url = "https://github.com/containers/fuse-overlayfs/archive/refs/tags/v1.18.tar.gz"

    license("GPL-3.0-or-later")

    version(
        "1.18",
        sha256="fdd1896c8de35a15eb14444d7880be81d635fcbbc4ad162d8bc3ccf5627aa8c7",
    )

    depends_on("c", type="build")  # generated

    depends_on("libfuse@3.2.1:", type=("build", "link"))
    depends_on("pkgconfig", type="build")

    # The git-tag archive ships only configure.ac; the configure script
    # must be regenerated at build time.
    depends_on("autoconf@:2.69", type="build")
    depends_on("automake", type="build")
    depends_on("libtool", type="build")
    depends_on("m4", type="build")

    # The bundled gnulib m4 files (2019 era) are incompatible with
    # autoconf >= 2.70: configure.ac then fails with "possibly undefined
    # macro: AC_DEFINE" because the old m4sugar no longer matches. The
    # autoconf pin above forces Spack to concretize its own 2.69 instead
    # of reusing whatever autotools version is already in the DAG.

    sanity_check_is_file = ["bin/fuse-overlayfs"]
