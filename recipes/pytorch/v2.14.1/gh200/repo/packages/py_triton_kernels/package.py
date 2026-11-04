# Copyright Spack Project Developers. See COPYRIGHT file for details.
#
# SPDX-License-Identifier: (Apache-2.0 OR MIT)

from spack_repo.builtin.build_systems.python import PythonPackage

from spack.package import *


class PyTritonKernels(PythonPackage):
    """Triton kernels (matmul_ogs, routing, swiglu, ...) shipped in the Triton
    source tree under python/triton_kernels. NGC installs it alongside triton."""

    homepage = "https://github.com/triton-lang/triton"
    url = "https://github.com/triton-lang/triton/archive/refs/tags/v3.8.0.tar.gz"

    license("MIT")

    # versioned by the triton release it is taken from (its own version is 1.0.0)
    version("3.8.0", sha256="d50981f98bf61a5ce21d2a0c6ac067c20b7f741acf3bee4b8370edc3b63fd337")

    depends_on("py-setuptools@64:", type="build")
    with default_args(type=("build", "run")):
        depends_on("py-numpy")
        depends_on("py-pytest")
        depends_on("py-triton@3.8.0", when="@3.8.0")
        depends_on("py-torch")

    build_directory = "python/triton_kernels"
