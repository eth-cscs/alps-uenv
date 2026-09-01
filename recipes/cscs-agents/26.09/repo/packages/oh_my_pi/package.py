# Copyright Spack Project Developers. See COPYRIGHT file for details.
#
# SPDX-License-Identifier: (Apache-2.0 OR MIT)

import os

from spack_repo.builtin.build_systems.generic import Package

from spack.package import *


class OhMyPi(Package):
    """Oh-My-Pi coding agent CLI."""

    homepage = "https://omp.sh"
    url = "https://github.com/can1357/oh-my-pi/releases/download/v18.0.9/LICENSE"

    license("MIT")

    sanity_check_is_file = ["bin/omp"]

    version(
        "18.0.9",
        sha256="16c45f9d667442781f03fa198914cc39abcaa48ec5ed8f644643e554ca2fbf63",
        expand=False,
    )

    resource(
        name="omp-linux-arm64",
        url="https://github.com/can1357/oh-my-pi/releases/download/v18.0.9/omp-linux-arm64",
        sha256="99cbd2b24b57f11029c345271b3c3adb7820f435f0229f6c577f503f2e64c12a",
        expand=False,
        placement={"omp-linux-arm64": "omp-linux-arm64"},
        when="@18.0.9 target=aarch64:",
    )
    resource(
        name="omp-linux-x64",
        url="https://github.com/can1357/oh-my-pi/releases/download/v18.0.9/omp-linux-x64",
        sha256="55304008876a61f48c2a1dc1b0998ca36e7e45b8bc25aa25cf24e5c44524412c",
        expand=False,
        placement={"omp-linux-x64": "omp-linux-x64"},
        when="@18.0.9 target=x86_64:",
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
