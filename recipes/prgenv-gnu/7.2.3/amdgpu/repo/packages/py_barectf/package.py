# Copyright Spack Project Developers. See COPYRIGHT file for details.
#
# SPDX-License-Identifier: (Apache-2.0 OR MIT)


from spack_repo.builtin.build_systems.python import PythonPackage

from spack.package import *


class PyBarectf(PythonPackage):
    """barectf (from bare metal and CTF) is a generator of
    tracer which produces CTF data streams."""

    homepage = "https://github.com/efficios/barectf"
    git = "https://github.com/efficios/barectf.git"

    license("MIT")

    version("3.1.2-fix", branch="master", commit="e16d289546bb4f6b0d909f79b8d6188eabe32640")

    depends_on("py-poetry-core", type=("build", "run"))
    depends_on("py-setuptools", type=("build", "run"))
    depends_on("py-termcolor@1.1:", type=("build", "run"))
    depends_on("py-pyyaml@6.0:", type=("build", "run"))
    depends_on("py-jsonschema@3.2:", type=("build", "run"))
    depends_on("py-jinja2@3.0:", type=("build", "run"))
