# Copyright Spack Project Developers. See COPYRIGHT file for details.
#
# SPDX-License-Identifier: (Apache-2.0 OR MIT)

from spack_repo.builtin.build_systems.generic import Package

from spack.package import *


class CscsAgentSkills(Package):
    """CSCS skills shared by the packaged coding agents."""

    homepage = "https://github.com/eth-cscs/agent-skills"
    url = "https://github.com/eth-cscs/agent-skills/archive/6d1c86ddf3ba2c785c27e03fce999c79c6af499f.tar.gz"

    license("MIT")

    version(
        "2026.07.13",
        sha256="a3538d1f91f5d483ba63b254c0e3cc28032fa468ddf144473796c8566426c29d",
    )

    phases = ["install"]

    def url_for_version(self, version):
        if str(version) == "2026.07.13":
            return "https://github.com/eth-cscs/agent-skills/archive/6d1c86ddf3ba2c785c27e03fce999c79c6af499f.tar.gz"

        return self.url

    def install(self, spec, prefix):
        share_dir = join_path(prefix.share, "cscs-agent-skills")
        skills_dir = join_path(share_dir, "skills")
        install_tree("skills", skills_dir)
        install("LICENSE", share_dir)
        install("README.md", share_dir)

        skill_dir = join_path(skills_dir, "refresh-cscs-models")
        mkdirp(skill_dir)
        with open(join_path(skill_dir, "SKILL.md"), "w", encoding="utf-8") as f:
            f.write(
                "---\n"
                "name: refresh-cscs-models\n"
                "description: Refresh CSCS inference model configuration for OpenCode or Oh-My-Pi. Use when agent model lists, context windows, pricing, or CSCS provider config look stale or missing.\n"
                "---\n"
                "\n"
                "# Refresh CSCS Model Configuration\n"
                "\n"
                "Use `cscs-agent-model-config` to regenerate CSCS inference provider config.\n"
                "It queries only metadata endpoints and never writes API keys to disk.\n"
                "\n"
                "Requirements:\n"
                "- Export `CSCS_INFERENCE_API_KEY` before refreshing. `CSCS_API_KEY` is accepted as a compatibility alias.\n"
                "- Generated files reference `CSCS_INFERENCE_API_KEY` by name; the secret value is not persisted.\n"
                "\n"
                "Useful commands:\n"
                "\n"
                "```bash\n"
                "# OpenCode config block\n"
                "cscs-agent-model-config --format opencode --out-dir /tmp/cscs-models\n"
                "\n"
                "# Oh-My-Pi models.yml provider block\n"
                "cscs-agent-model-config --format pi --out-dir /tmp/cscs-models\n"
                "\n"
                "# Human-readable model table\n"
                "cscs-agent-model-config --format table\n"
                "```\n"
                "\n"
                "The `opencode-bwrap` and `omp-bwrap` launchers seed static CSCS defaults and refresh their managed config files opportunistically. If a managed file was edited by the user, the launcher stops overwriting it.\n"
            )
