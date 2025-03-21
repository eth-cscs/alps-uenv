# Copyright 2013-2024 Lawrence Livermore National Security, LLC and other
# Spack Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: (Apache-2.0 OR MIT)

from spack.package import *


class PyWandb(PythonPackage):
    """A tool for visualizing and tracking your machine
    learning experiments."""

    homepage = "https://github.com/wandb/wandb"
    pypi = "wandb/wandb-0.13.9.tar.gz"

    maintainers("thomas-bouvier")

    license("MIT")

    version("0.19.8", sha256="3a4844bb38758657b94b090e72ee355fe5b926e3a048232f0ca4248f801d8d80")
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

    # Historical dependencies
    depends_on("py-pathtools", type=("build", "run"), when="@:0.15")
