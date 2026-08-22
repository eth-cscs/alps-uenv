# Copyright Spack Project Developers. See COPYRIGHT file for details.
#
# SPDX-License-Identifier: (Apache-2.0 OR MIT)

from spack_repo.builtin.build_systems.generic import Package

from spack.package import *


class OpencodeBwrap(Package):
    """Bubblewrap-based launcher for OpenCode with separate XDG state."""

    homepage = "https://opencode.ai"
    has_code = False

    license("MIT")

    version("1.18.20")
    version("1.18.3")

    depends_on("opencode@1.18.20", when="@1.18.20", type="run")
    depends_on("opencode@1.18.3", when="@1.18.3", type="run")
    depends_on("bubblewrap", type="run")
    depends_on("ripgrep", type="run")

    def install(self, spec, prefix):
        mkdirp(prefix.bin)

        template = join_path(self.package_dir, "opencode-bwrap.in")
        with open(template, "r", encoding="utf-8") as f:
            script = f.read()

        replacements = {
            "@OPENCODE@": str(spec["opencode"].prefix.bin.opencode),
            "@BWRAP@": str(spec["bubblewrap"].prefix.bin.bwrap),
            "@OPENCODE_BIN@": str(spec["opencode"].prefix.bin),
            "@RIPGREP_BIN@": str(spec["ripgrep"].prefix.bin),
        }

        for token, value in replacements.items():
            script = script.replace(token, value)

        launcher = join_path(prefix.bin, "opencode-bwrap")
        with open(launcher, "w", encoding="utf-8") as f:
            f.write(script)
        set_executable(launcher)
