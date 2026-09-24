# Copyright Spack Project Developers. See COPYRIGHT file for details.
#
# SPDX-License-Identifier: (Apache-2.0 OR MIT)

from spack_repo.builtin.build_systems.python import PythonPackage

from spack.package import *


class PyNvidiaCudnnFrontend(PythonPackage):
    """Python and header-only C++ frontend for the cuDNN graph API."""

    homepage = "https://github.com/NVIDIA/cudnn-frontend"
    url = "https://files.pythonhosted.org/packages/d1/9e/33b746b800c36a8aae8432605c5b2af6cc5fc683cc1a6954a084c3853690/nvidia_cudnn_frontend-1.28.0-cp312-cp312-manylinux_2_27_aarch64.manylinux_2_28_aarch64.whl"

    license("Apache-2.0 AND MIT")

    version("1.28.0", sha256="060b0c021f6841312ad26dd837a51b4941d4e0d2a547d87455bd974c173da075")

    depends_on("python@3.12", type=("build", "run"))
    depends_on("py-setuptools", type="build")
    depends_on("cudnn@8.5:", type=("build", "link", "run"))
