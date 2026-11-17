# Copyright Spack Project Developers. See COPYRIGHT file for details.
#
# SPDX-License-Identifier: (Apache-2.0 OR MIT)

import os

from spack_repo.builtin.build_systems.generic import Package

from spack.package import *


class Opencode(Package):
    """OpenCode terminal agent, packaged from upstream's native npm artifacts."""

    homepage = "https://opencode.ai"
    url = "https://raw.githubusercontent.com/anomalyco/opencode/v2.1.0/LICENSE"
    supplier = "Organization: Anomaly Innovations"

    maintainers("aprozo")

    license("MIT", checked_by="aprozo")

    version(
        "2.1.0",
        sha256="625f0f619133f89bbbb2abe37369613dfa1885eba1e50d02170deb62bb42cb6b",
        expand=False,
    )

    conflicts("platform=darwin")
    depends_on("ripgrep", type="run")

    resource(
        name="opencode-linux-arm64",
        url="https://registry.npmjs.org/@opencode/cli-linux-arm64/-/cli-linux-arm64-2.1.0.tgz",
        sha256="07cc6b6bd7178b45c9916c4ab8a038951d304753bdf798cd7a63d69b22eed326",
        placement="release",
        when="@2.1.0 platform=linux target=aarch64:",
    )
    resource(
        name="opencode-linux-x64",
        url="https://registry.npmjs.org/@opencode/cli-linux-x64/-/cli-linux-x64-2.1.0.tgz",
        sha256="da129a76ade124babf84f3932bf6080edf14b94d40f1953fdbb057e88b5252ee",
        placement="release",
        when="@2.1.0 platform=linux target=x86_64:",
    )

    phases = ["install"]
    sanity_check_is_file = ["bin/opencode"]

    def install(self, spec, prefix):
        if not (
            spec.satisfies("platform=linux target=aarch64:")
            or spec.satisfies("platform=linux target=x86_64:")
        ):
            raise InstallError("opencode only packages upstream Linux x86_64 and arm64 archives")

        binary = join_path(self.stage.source_path, "release", "bin", "opencode")
        if not os.path.isfile(binary):
            raise InstallError("expected OpenCode npm artifact was not staged")

        mkdirp(prefix.bin)
        install(binary, prefix.bin)
        set_executable(join_path(prefix.bin, "opencode"))
        licenses = join_path(prefix.share, "licenses", "opencode")
        mkdirp(licenses)
        install(join_path(self.stage.source_path, "LICENSE"), licenses)

    def setup_run_environment(self, env):
        env.set("OPENCODE_DISABLE_AUTOUPDATE", "true")
