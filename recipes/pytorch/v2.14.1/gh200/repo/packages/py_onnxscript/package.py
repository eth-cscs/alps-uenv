# Copyright Spack Project Developers. See COPYRIGHT file for details.
#
# SPDX-License-Identifier: (Apache-2.0 OR MIT)

from spack_repo.builtin.build_systems.python import PythonPackage

from spack.package import *


class PyOnnxscript(PythonPackage):
    """Naturally author ONNX functions and models using a subset of Python"""

    homepage = "https://github.com/microsoft/onnxscript"
    git = "https://github.com/microsoft/onnxscript.git"
    # PyPI sdist: the GitHub repository (and its tag tarballs) returned 404 on 2026-11-25
    pypi = "onnxscript/onnxscript-0.5.6.tar.gz"

    license("MIT")

    version("0.5.6", sha256="cc3338b2976daffd2af0bb6ac4866a4dca76aefface1666a0d7bc65ad9850822")

    depends_on("python@3.9:", type=("build", "run"))
    depends_on("py-setuptools@70:", type="build")

    depends_on("py-numpy", type=("build", "run"))
    depends_on("py-onnx@1.16:", type=("build", "run"))
    depends_on("py-onnx-ir@0.1.12:", type=("build", "run"))
    depends_on("py-packaging", type=("build", "run"))
    depends_on("py-typing-extensions@4.10:", type=("build", "run"))
    depends_on("py-ml-dtypes", type=("build", "run"))

    def setup_build_environment(self, env: EnvironmentModifications) -> None:
        # Otherwise setup.py appends a ".dev<date>" suffix to the version
        env.set("ONNX_SCRIPT_RELEASE", "1")
