# Copyright Spack Project Developers. See COPYRIGHT file for details.
#
# SPDX-License-Identifier: (Apache-2.0 OR MIT)

from spack_repo.builtin.build_systems.python import PythonPackage

from spack.package import *


class PyTyro(PythonPackage):
    """CLI interfaces and config objects generated from Python type hints."""

    homepage = "https://github.com/brentyi/tyro"
    pypi = "tyro/tyro-1.0.15.tar.gz"

    license("MIT")

    # 1.0.15 is the version in NGC pytorch 26.07
    version("1.0.15", sha256="3f1d60887723eecb9c489f195d11f079c4a1f33df74b723552ad31ec57c667bb")

    depends_on("python@3.8:", type=("build", "run"))
    depends_on("py-hatchling", type="build")
    with default_args(type=("build", "run")):
        depends_on("py-docstring-parser@0.16:")
        depends_on("py-typeguard@4:")
        depends_on("py-typing-extensions@4.13:")
