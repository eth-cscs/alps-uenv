# Copyright Spack Project Developers. See COPYRIGHT file for details.
#
# SPDX-License-Identifier: (Apache-2.0 OR MIT)

import os

from spack_repo.builtin.build_systems.generic import Package

from spack.package import *


class OhMyPi(Package):
    """Oh-My-Pi coding agent CLI."""

    homepage = "https://omp.sh"
    url = "https://github.com/can1357/oh-my-pi/releases/download/v18.0.5/LICENSE"

    license("MIT")

    sanity_check_is_file = ["bin/omp"]

    version(
        "18.0.5",
        sha256="16c45f9d667442781f03fa198914cc39abcaa48ec5ed8f644643e554ca2fbf63",
        expand=False,
    )

    resource(
        name="omp-linux-arm64",
        url="https://github.com/can1357/oh-my-pi/releases/download/v18.0.5/omp-linux-arm64",
        sha256="9fa632da09cc6f2b625bb79aa291d52985f936a10408d278d550983f91460785",
        expand=False,
        placement={"omp-linux-arm64": "omp-linux-arm64"},
        when="@18.0.5 target=aarch64:",
    )
    resource(
        name="omp-linux-x64",
        url="https://github.com/can1357/oh-my-pi/releases/download/v18.0.5/omp-linux-x64",
        sha256="d5a322af241cebe2662b3b792ff29d3ea6e61364328e916c9429065f346391ed",
        expand=False,
        placement={"omp-linux-x64": "omp-linux-x64"},
        when="@18.0.5 target=x86_64:",
    )

    phases = ["install"]

    def content_hash(self, content=None):
        if content is None:
            with open(join_path(self.package_dir, "package.py"), "rb") as f:
                content = f.read()

        return super().content_hash(content=content)

    def patch_scrollback_clear(self, binary):
        """Prevent OMP from erasing native terminal scrollback with ED3."""
        with open(binary, "rb") as f:
            contents = f.read()

        patched = contents.replace(b"\x1b[3J", b"\x1b[0m")
        if patched == contents:
            raise InstallError("expected OMP binary to contain ED3 scrollback-clear sequence")

        with open(binary, "wb") as f:
            f.write(patched)

    def install(self, spec, prefix):
        if spec.satisfies("target=aarch64:"):
            binary = "omp-linux-arm64"
        elif spec.satisfies("target=x86_64:"):
            binary = "omp-linux-x64"
        else:
            raise InstallError("oh-my-pi only packages upstream Linux x86_64 and arm64 binaries")

        if not os.path.isfile(binary):
            raise InstallError("expected release asset was not staged: {0}".format(binary))

        mkdirp(prefix.bin)
        installed_binary = join_path(prefix.bin, "omp")
        install(binary, installed_binary)
        self.patch_scrollback_clear(installed_binary)
        set_executable(installed_binary)
