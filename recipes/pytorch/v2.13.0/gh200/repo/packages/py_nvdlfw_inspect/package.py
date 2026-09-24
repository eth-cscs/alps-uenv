# Copyright Spack Project Developers. See COPYRIGHT file for details.
#
# SPDX-License-Identifier: (Apache-2.0 OR MIT)

from spack_repo.builtin.build_systems.python import PythonPackage

from spack.package import *


class PyNvdlfwInspect(PythonPackage):
    """Debugging utilities for NVIDIA deep-learning frameworks."""

    homepage = "https://github.com/NVIDIA/nvidia-dlfw-inspect"
    url = "https://files.pythonhosted.org/packages/8a/86/94188e03e5d4dd7b73c390b0cddcde5618b3799c18e327b2bf15763f6137/nvdlfw_inspect-0.2.2-py3-none-any.whl"

    license("Apache-2.0")

    version("0.2.2", sha256="8a4dc2814c5a4cd19ae304170b9bfa514538ef3c3eb243a45a82404ec3cb279d")

    depends_on("python@3.8:", type=("build", "run"))
    depends_on("py-setuptools", type="build")
    depends_on("py-pyyaml@6:", type=("build", "run"))
    depends_on("py-torch@2.1:", type=("build", "run"))
