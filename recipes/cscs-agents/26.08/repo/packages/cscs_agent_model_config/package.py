# Copyright Spack Project Developers. See COPYRIGHT file for details.
#
# SPDX-License-Identifier: (Apache-2.0 OR MIT)

import os

from spack_repo.builtin.build_systems.generic import Package

from spack.package import *


class CscsAgentModelConfig(Package):
    """Runtime generator and static defaults for CSCS agent model config."""

    homepage = "https://docs.cscs.ch/services/inference/api/"
    has_code = False

    license("MIT")

    version("2026.08.26")


    def _source_script(self):
        return join_path(self.package_dir, "cscs_models.py")

    def _launcher_template(self):
        return join_path(self.package_dir, "cscs-agent-model-config.in")

    def content_hash(self, content=None):
        if content is None:
            with open(join_path(self.package_dir, "package.py"), "rb") as f:
                content = f.read()

        paths = [self._source_script(), self._launcher_template()]
        defaults_dir = join_path(self.package_dir, "files")
        for root, _, filenames in os.walk(defaults_dir):
            for filename in filenames:
                paths.append(join_path(root, filename))

        for path in sorted(paths):
            relpath = os.path.relpath(path, self.package_dir)
            with open(path, "rb") as f:
                content += (
                    b"\n_cscs_agent_model_config_file = "
                    + repr((relpath, f.read())).encode("utf-8")
                    + b"\n"
                )

        return super().content_hash(content=content)


    def install(self, spec, prefix):
        mkdirp(prefix.bin)
        defaults = join_path(prefix.share, "cscs-agent-model-config", "defaults")
        script_target = join_path(prefix.share, "cscs-agent-model-config", "cscs_models.py")
        mkdirp(defaults)

        script = self._source_script()
        install(script, script_target)
        install_tree(join_path(self.package_dir, "files"), defaults)

        with open(self._launcher_template(), "r", encoding="utf-8") as f:
            launcher_script = f.read()
        launcher_script = launcher_script.replace("@CSCS_MODELS_SCRIPT@", script_target)
        if "@CSCS_MODELS_SCRIPT@" in launcher_script:
            raise InstallError("unresolved CSCS model generator path")

        launcher = join_path(prefix.bin, "cscs-agent-model-config")
        with open(launcher, "w", encoding="utf-8") as f:
            f.write(launcher_script)
        set_executable(launcher)
