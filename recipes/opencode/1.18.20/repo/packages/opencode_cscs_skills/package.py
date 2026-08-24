# Copyright Spack Project Developers. See COPYRIGHT file for details.
#
# SPDX-License-Identifier: (Apache-2.0 OR MIT)

from spack_repo.builtin.build_systems.generic import Package

from spack.package import *


class OpencodeCscsSkills(Package):
    """CSCS agent skills packaged for OpenCode."""

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
        install_tree("skills", prefix.share.opencode.skills)
        install("LICENSE", prefix.share.opencode)
        install("README.md", prefix.share.opencode)
