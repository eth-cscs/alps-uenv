# Copyright 2013-2024 Lawrence Livermore National Security, LLC and other
# Spack Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: (Apache-2.0 OR MIT)

import platform
import sys

from spack.package import *

arch, os = platform.machine(), sys.platform

class PyWandb(PythonPackage):
    """A tool for visualizing and tracking your machine
    learning experiments."""

    homepage = "https://github.com/wandb/wandb"
    pypi = "wandb/wandb-0.13.9.tar.gz"

    maintainers("thomas-bouvier")

    license("MIT")

    if (arch == "x86_64" or arch == "x64") and os == "linux":
        version(
            "0.19.9",
            sha256="5dc6c7180a5bf1eb5bd9cab8a1886fd980c76d54253c967082fe19d197443a2d",
            url="https://files.pythonhosted.org/packages/89/d0/737d26d709bd7bc3f6b2250f41fda3d0787239cfdbd6eb13057c64c81ace/wandb-0.19.9-py3-none-manylinux_2_17_x86_64.manylinux2014_x86_64.whl",
            expand=False,
        )
    elif arch == "aarch64" and os == "linux":
        version(
            "0.19.9",
            sha256="8a074ad070c4e8cbb03b2149a98abbe2d7562220f095a21c736e1abbca399eef",
            url="https://files.pythonhosted.org/packages/56/07/47ab3b4f0f4a32d9269ecb60aa71da3e426faa2abe51c4f000778e2696c3/wandb-0.19.9-py3-none-manylinux_2_17_aarch64.manylinux2014_aarch64.whl",
            expand=False,
        )
    version("0.16.6", sha256="86f491e3012d715e0d7d7421a4d6de41abef643b7403046261f962f3e512fe1c")
    version("0.13.9", sha256="0a17365ce1f18306ce7a7f16b943094fac7284bb85f4e52c0685705602f9e307")

    depends_on("py-setuptools", type=("build", "run"))

    depends_on("py-setproctitle", type=("build", "run"))
    depends_on("py-appdirs@1.4.3:", type=("build", "run"))
    depends_on("py-protobuf@3.19:", type=("build", "run"))
    conflicts("^py-protobuf@4.21.0")
    conflicts("^py-protobuf@5.28.0")
    depends_on("py-typing-extensions", type=("build", "run"), when="^python@:3.9")

    depends_on("py-pyyaml", type=("build", "run"))
    depends_on("py-click@7:", type=("build", "run"), when="@0.13")
    depends_on("py-click@7.1:", type=("build", "run"), when="@0.15.5:")
    conflicts("^py-click@8.0.0")
    depends_on("py-gitpython@1:", type=("build", "run"))
    conflicts("^py-gitpython@3.1.29")
    depends_on("py-requests@2", type=("build", "run"))
    depends_on("py-psutil@5:", type=("build", "run"))
    depends_on("py-sentry-sdk@1.0.0:", type=("build", "run"))
    depends_on("py-sentry-sdk@2:", type=("build", "run"), when="@0.19.8:")
    depends_on("py-dockerpy-creds@0.4.0:", type=("build", "run"))
    depends_on("py-platformdirs", type=("build", "run"))
    depends_on("py-pydantic@2.6:", type=("build", "run"))
    depends_on("py-psutil", type=("build", "run"))

    # Historical dependencies
    depends_on("py-pathtools", type=("build", "run"), when="@:0.15")
