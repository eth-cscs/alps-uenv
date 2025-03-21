# Copyright 2013-2024 Lawrence Livermore National Security, LLC and other
# Spack Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: (Apache-2.0 OR MIT)

from spack.package import *


class PyTroveClassifiers(PythonPackage):
    """The trove-classifiers pacakge is the canonical source for classifiers
    on PyPI. Classifiers categorize projects per PEP 301."""

    homepage = "https://github.com/pypa/trove-classifiers"
    pypi = "trove-classifiers/trove_classifiers-2025.3.19.19.tar.gz"

    license("Apache-2.0")

    version("2025.3.19.19", sha256="98e9d396fe908d5f43b7454fa4c43d17cd0fdadf046f45fb38a5e3af8d959ecd")
    version("2023.8.7", sha256="c9f2a0a85d545e5362e967e4f069f56fddfd91215e22ffa48c66fb283521319a")
    version("2023.3.9", sha256="ee42f2f8c1d4bcfe35f746e472f07633570d485fab45407effc0379270a3bb03")

    depends_on("py-setuptools", type="build")
    depends_on("py-calver", type="build")
