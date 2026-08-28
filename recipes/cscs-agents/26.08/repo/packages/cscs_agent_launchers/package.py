# Copyright Spack Project Developers. See COPYRIGHT file for details.
#
# SPDX-License-Identifier: (Apache-2.0 OR MIT)

import os
import re

from spack_repo.builtin.build_systems.generic import Package

from spack.package import *


class CscsAgentLaunchers(Package):
    """Bubblewrap launchers for OpenCode and Oh-My-Pi on CSCS systems."""

    homepage = "https://docs.cscs.ch"
    has_code = False

    license("MIT")

    version("2026.08.28")

    depends_on("opencode@1.18.25", type="run")
    depends_on("oh-my-pi@18.0.9", type="run")
    depends_on("bubblewrap", type="run")
    depends_on("cscs-agent-model-config", type="run")
    depends_on("cscs-agent-skills", type="run")
    depends_on("ripgrep", type="run")

    sanity_check_is_file = ["bin/opencode-bwrap", "bin/omp-bwrap"]

    def content_hash(self, content=None):
        if content is None:
            with open(join_path(self.package_dir, "package.py"), "rb") as f:
                content = f.read()

        paths = [join_path(self.package_dir, "agent-bwrap.in")]
        defaults_dir = join_path(self.package_dir, "files")
        for root, _, filenames in os.walk(defaults_dir):
            for filename in filenames:
                paths.append(join_path(root, filename))

        for path in sorted(paths):
            relpath = os.path.relpath(path, self.package_dir)
            with open(path, "rb") as f:
                content += (
                    b"\n_cscs_agent_launcher_file = "
                    + repr((relpath, f.read())).encode("utf-8")
                    + b"\n"
                )

        return super().content_hash(content=content)

    def install(self, spec, prefix):
        defaults = join_path(prefix.share, "cscs-agent-launchers", "defaults")
        mkdirp(prefix.bin)
        install_tree(join_path(self.package_dir, "files"), defaults)

        with open(join_path(self.package_dir, "agent-bwrap.in"), "r", encoding="utf-8") as f:
            script = f.read()

        replacements = {
            "@OPENCODE@": str(spec["opencode"].prefix.bin.opencode),
            "@OMP@": str(spec["oh-my-pi"].prefix.bin.omp),
            "@BWRAP@": str(spec["bubblewrap"].prefix.bin.bwrap),
            "@CSCS_MODEL_CONFIG@": join_path(
                spec["cscs-agent-model-config"].prefix.bin,
                "cscs-agent-model-config",
            ),
            "@CSCS_MODEL_DEFAULTS@": join_path(
                spec["cscs-agent-model-config"].prefix.share,
                "cscs-agent-model-config",
                "defaults",
            ),
            "@LAUNCHER_DEFAULTS@": defaults,
            "@CSCS_SKILLS@": join_path(
                spec["cscs-agent-skills"].prefix.share,
                "cscs-agent-skills",
                "skills",
            ),
            "@OPENCODE_BIN@": str(spec["opencode"].prefix.bin),
            "@OMP_BIN@": str(spec["oh-my-pi"].prefix.bin),
            "@RIPGREP_BIN@": str(spec["ripgrep"].prefix.bin),
        }
        for token, value in replacements.items():
            script = script.replace(token, value)
        unresolved = sorted(set(re.findall(r"@[A-Z][A-Z_]+@", script)))
        if unresolved:
            raise InstallError(
                "unresolved launcher template tokens: {0}".format(", ".join(unresolved))
            )

        for name in ("opencode-bwrap", "omp-bwrap"):
            launcher = join_path(prefix.bin, name)
            with open(launcher, "w", encoding="utf-8") as f:
                f.write(script)
            set_executable(launcher)
