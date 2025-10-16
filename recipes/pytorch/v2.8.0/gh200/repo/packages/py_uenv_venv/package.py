# Copyright Spack Project Developers. See COPYRIGHT file for details.
#
# SPDX-License-Identifier: (Apache-2.0 OR MIT)

from spack_repo.builtin.build_systems.python import PythonPackage

from spack.package import *

class PyUenvVenv(PythonPackage):

    homepage = "https://github.com/boeschf/uenv_venv.git"
    git = "https://github.com/boeschf/uenv_venv.git"

    version("main", branch="main")

    license("MIT")

    depends_on("python@3.9:", type=("build", "run"))
    depends_on("py-setuptools@61:", type="build")
    depends_on("py-wheel", type="build")

    import_modules = ["uenv_venv"]
