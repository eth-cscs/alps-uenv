# Copyright Spack Project Developers. See COPYRIGHT file for details.
#
# SPDX-License-Identifier: (Apache-2.0 OR MIT)

from spack_repo.builtin.build_systems.python import PythonPackage

from spack.package import *


class PyOnnxIr(PythonPackage):
    """Efficient in-memory representation for ONNX"""

    homepage = "https://github.com/onnx/ir-py"
    git = "https://github.com/onnx/ir-py.git"
    url = "https://github.com/onnx/ir-py/archive/refs/tags/v0.1.12.tar.gz"

    license("Apache-2.0")

    version("0.1.12", sha256="f37f76198c7bfd0b9ad2e796ecebd4c4c4a6a180b134e8921d795a919b790d06")

    depends_on("python@3.9:", type=("build", "run"))
    depends_on("py-setuptools", type="build")

    depends_on("py-numpy", type=("build", "run"))
    depends_on("py-onnx@1.16:", type=("build", "run"))
    depends_on("py-typing-extensions@4.10:", type=("build", "run"))
    depends_on("py-ml-dtypes@0.5:", type=("build", "run"))
