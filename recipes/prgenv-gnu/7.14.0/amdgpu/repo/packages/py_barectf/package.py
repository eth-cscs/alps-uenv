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

    # archive of the commit, not a git checkout: py-poetry-core sets GIT_DIR in
    # the build env of its dependents, and spack 1.2 fetches inside that env,
    # so a git fetch fails during the build
    version(
        "3.1.2-fix",
        url="https://github.com/efficios/barectf/archive/e16d289546bb4f6b0d909f79b8d6188eabe32640.tar.gz",
        sha256="1047b4233519fe46511a44203d7968d7cfaaf6a7f42dabdaab4c0f5d1e2cdc14",
    )

    depends_on("py-poetry-core", type=("build", "run"))
    depends_on("py-setuptools", type=("build", "run"))
    depends_on("py-termcolor@1.1:", type=("build", "run"))
    depends_on("py-pyyaml@6.0:", type=("build", "run"))
    depends_on("py-jsonschema@3.2:", type=("build", "run"))
    depends_on("py-jinja2@3.0:", type=("build", "run"))
