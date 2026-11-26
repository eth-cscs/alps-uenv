# Copyright Spack Project Developers. See COPYRIGHT file for details.
#
# SPDX-License-Identifier: (Apache-2.0 OR MIT)

from spack_repo.builtin.build_systems.python import PythonPackage

from spack.package import *


class PyTorchdata(PythonPackage):
    """Composable data loading modules for PyTorch (StatefulDataLoader, nodes).
    Only a pure-python wheel is published for 0.11."""

    homepage = "https://github.com/pytorch/data"
    url = "https://files.pythonhosted.org/packages/95/d4/af694ef718aedbe95a72760ab9ff7a6a7a44ace2d7f70c27bfeb67c5c503/torchdata-0.11.0-py3-none-any.whl"

    license("BSD-3-Clause")

    # 0.11.0 is the version in NGC pytorch 26.07
    version(
        "0.11.0",
        sha256="52b940fbbe0e00fb21cabddf528449d1bec5bfb0d0823b7487b15f951658ee33",
        expand=False,
    )

    depends_on("python@3.9:", type=("build", "run"))
    with default_args(type=("build", "run")):
        depends_on("py-urllib3@1.25:")
        depends_on("py-requests")
        depends_on("py-torch@2:")
