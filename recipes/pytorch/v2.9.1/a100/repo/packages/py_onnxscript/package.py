# Copyright Spack Project Developers. See COPYRIGHT file for details.
#
# SPDX-License-Identifier: (Apache-2.0 OR MIT)

from spack_repo.builtin.build_systems.python import PythonPackage

from spack.package import *


class PyOnnxscript(PythonPackage):
    """Naturally author ONNX functions and models using a subset of Python"""

    homepage = "https://github.com/microsoft/onnxscript"
    git = "https://github.com/microsoft/onnxscript.git"
    url = "https://github.com/microsoft/onnxscript/archive/refs/tags/v0.5.6.tar.gz"

    license("MIT")

    version("0.5.6", sha256="63d2fd27c05dc0f8f483ffc21f239f0c600ad7dc152acdbc2d151e88583f6a91")

    depends_on("python@3.9:", type=("build", "run"))
    depends_on("py-setuptools@70:", type="build")

    depends_on("py-numpy", type=("build", "run"))
    depends_on("py-onnx@1.16:", type=("build", "run"))
    depends_on("py-onnx-ir@0.1.12:", type=("build", "run"))
    depends_on("py-packaging", type=("build", "run"))
    depends_on("py-typing-extensions@4.10:", type=("build", "run"))
    depends_on("py-ml-dtypes", type=("build", "run"))
