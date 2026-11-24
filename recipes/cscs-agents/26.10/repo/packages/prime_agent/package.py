# Copyright Spack Project Developers. See COPYRIGHT file for details.
#
# SPDX-License-Identifier: (Apache-2.0 OR MIT)

import os

from spack_repo.builtin.build_systems.generic import Package

from spack.package import *


class PrimeAgent(Package):
    """Prime Agent is a terminal coding agent with persistent background workers."""

    homepage = "https://github.com/PrimeIntellect-ai/prime-agent"
    url = "https://raw.githubusercontent.com/PrimeIntellect-ai/prime-agent/v0.10.0/LICENSE"
    supplier = "Organization: Prime Intellect"

    license("MIT")

    version(
        "0.10.0",
        sha256="e0d1bf8d137e6d56e98ee968402b0b7f324c5c85ea505e4fd7b6b78615bc4e7a",
        expand=False,
    )

    conflicts("platform=darwin")

    resource(
        name="prime-agent-linux-arm64",
        url="https://github.com/PrimeIntellect-ai/prime-agent/releases/download/v0.10.0/prime-agent-0.10.0-linux-arm64.tar.gz",
        sha256="f3cab3530a4d7ca43dbef8321bf13f260d1ba05d8b5dde057165a20bd4f675c4",
        placement="release",
        when="@0.10.0 platform=linux target=aarch64:",
    )
    resource(
        name="prime-agent-linux-x64",
        url="https://github.com/PrimeIntellect-ai/prime-agent/releases/download/v0.10.0/prime-agent-0.10.0-linux-x64.tar.gz",
        sha256="c16bd2af5e77b53f49b914a44742c4cf6a67c5ed5000041430b78dbd4c3bcbec",
        placement="release",
        when="@0.10.0 platform=linux target=x86_64:",
    )

    phases = ["install"]

    sanity_check_is_file = [
        "bin/prime-agent",
        "libexec/prime-agent/prime-agent",
        "libexec/prime-agent/prime-agent-runtime/pyproject.toml",
        "libexec/prime-agent/models.bundled.json",
    ]

    def install(self, spec, prefix):
        if not (spec.satisfies("target=aarch64:") or spec.satisfies("target=x86_64:")):
            raise InstallError("prime-agent only packages upstream Linux x86_64 and arm64 archives")

        release = join_path(self.stage.source_path, "release")
        binary = join_path(release, "prime-agent")
        if not os.path.isfile(binary):
            raise InstallError("expected Prime Agent release archive was not staged")

        app = join_path(prefix.libexec, "prime-agent")
        mkdirp(prefix.bin)
        install_tree(release, app)
        set_executable(join_path(app, "prime-agent"))

        launcher = join_path(prefix.bin, "prime-agent")
        with open(launcher, "w", encoding="utf-8") as f:
            f.write("#!/bin/sh\n")
            f.write('exec "{0}" "$@"\n'.format(join_path(app, "prime-agent")))
        set_executable(launcher)

    def setup_run_environment(self, env):
        env.set("PI_SKIP_VERSION_CHECK", "1")
