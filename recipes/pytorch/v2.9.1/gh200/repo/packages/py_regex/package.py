# Copyright Spack Project Developers. See COPYRIGHT file for details.
#
# SPDX-License-Identifier: (Apache-2.0 OR MIT)

from spack_repo.builtin.build_systems.python import PythonPackage

from spack.package import *


class PyRegex(PythonPackage):
    """Alternative regular expression module, to replace re."""

    homepage = "https://github.com/mrabarnett/mrab-regex"
    git = "https://github.com/mrabarnett/mrab-regex.git"

    license("Apache-2.0")

    version("2025.11.3", tag="2025.11.3", commit="b01d6e7349f1f754f9576e85aa19575acff0c839")
    version("2025.10.23", tag="2025.10.23", commit="26454da3a67572197648032fe5e7f9a288fa4a0f")
    version("2025.9.20", tag="2025.9.20", commit="4359a6a565e6725a899a4e1179c75fdad09030ae")
    version("2025.7.34", tag="2025.5.18", commit="23ca191dd8d259a42bc3dcae092e4eafce48652d")
    version("2025.5.18", tag="2025.5.18", commit="addaa7c484bffc2dd0844945e9bc756e1441c958")
    version("2024.11.6", tag="2024.11.6", commit="930983aa68ffc133ec086ef16cabdbb9c0c491ea")

    depends_on("c", type="build")  # generated

    depends_on("py-setuptools@77.0.3:", when="@2025.7.32:", type="build")
    depends_on("py-setuptools@61:", type="build")
    depends_on("python@3.9:", when="@2025.5.18:", type=("build", "run"))
    depends_on("python@3.8:", when="@2024.11.6:", type=("build", "run"))
    depends_on("python@3.6:", when="@2022.8.17:", type=("build", "run"))
