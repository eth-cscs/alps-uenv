# Copyright Spack Project Developers. See COPYRIGHT file for details.
#
# SPDX-License-Identifier: (Apache-2.0 OR MIT)

from spack_repo.builtin.build_systems.generic import Package

from spack.package import *


class CscsAgentSkills(Package):
    """CSCS skills shared by the packaged coding agents."""

    homepage = "https://github.com/eth-cscs/agent-skills"
    url = "https://github.com/eth-cscs/agent-skills/archive/62b583eb3407f6266198db5d22244a233741aa45.tar.gz"

    license("MIT")

    version(
        "2026.09.01",
        sha256="2a405bc4fa68ae83078515e806b0bca8d59e194f0bb6d348cebbae8f02be0801",
    )

    phases = ["install"]

    def url_for_version(self, version):
        if str(version) == "2026.09.01":
            return "https://github.com/eth-cscs/agent-skills/archive/62b583eb3407f6266198db5d22244a233741aa45.tar.gz"

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
                "description: Refresh CSCS production and experimental Forno inference model configuration for OpenCode or Oh-My-Pi. Use when agent model lists, context windows, pricing, or CSCS provider config look stale or missing.\n"
                "---\n"
                "\n"
                "# Refresh CSCS Model Configuration\n"
                "\n"
                "Use `cscs-agent-model-config` to regenerate CSCS production and Forno inference provider config.\n"
                "It queries only metadata endpoints and never writes API keys to disk.\n"
                "\n"
                "Requirements:\n"
                "- Export `CSCS_INFERENCE_API_KEY` for production and/or `CSCS_INFERENCE_API_KEY_FORNO` for Forno. `CSCS_API_KEY` remains a production compatibility alias.\n"
                "- Generated files reference the corresponding environment-variable names; secret values are not persisted.\n"
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
                "The `opencode-bwrap` and `omp-bwrap` launchers seed static production defaults and refresh their managed config files opportunistically. Adding or removing a gateway key triggers immediate regeneration. If a managed file was edited by the user, the launcher stops overwriting it.\n"
            )
