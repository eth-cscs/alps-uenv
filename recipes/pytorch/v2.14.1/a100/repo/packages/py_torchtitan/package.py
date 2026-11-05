# Copyright Spack Project Developers. See COPYRIGHT file for details.
#
# SPDX-License-Identifier: (Apache-2.0 OR MIT)

from spack_repo.builtin.build_systems.python import PythonPackage

from spack.package import *


class PyTorchtitan(PythonPackage):
    """A PyTorch native platform for large-scale generative AI model training."""

    homepage = "https://github.com/pytorch/torchtitan"
    pypi = "torchtitan/torchtitan-0.2.2.tar.gz"

    license("BSD-3-Clause")

    # 0.2.2 is the version in NGC pytorch 26.07
    version("0.2.2", sha256="f96babf03ce954dbd9078dab04eed61874c9144e23152bebca7be508de9eefd4")

    depends_on("python@3.10:", type=("build", "run"))
    depends_on("py-setuptools", type="build")
    with default_args(type=("build", "run")):
        depends_on("py-torch")
        depends_on("py-torchdata@0.8:")
        depends_on("py-datasets@2.21:")
        depends_on("py-tokenizers")
        depends_on("py-tomli@1.1:")
        depends_on("py-fsspec")
        depends_on("py-tyro")
        depends_on("py-tensorboard")
        depends_on("py-einops")
        depends_on("py-pillow")
