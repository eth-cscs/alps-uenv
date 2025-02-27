# Copyright Spack Project Developers. See COPYRIGHT file for details.
#
# SPDX-License-Identifier: (Apache-2.0 OR MIT)

from spack.package import *


class PyTensorstore(PythonPackage):
    """Read and write large, multi-dimensional arrays."""

    homepage = "https://github.com/google/tensorstore"
    pypi = "tensorstore/tensorstore-0.1.54.tar.gz"

    license("Apache-2.0")

    version("0.1.71", sha256="5c37c7b385517b568282a7aedded446216335d0cb41187c93c80b53596c92c96")
    #version("0.1.69", sha256="150cdc7e2044b7629ea466bfc8425ab50e52c8300950dbdd4a64445a2d4fbab1")
    #version("0.1.68", sha256="6e13d3e3c8fb6ed67712835a343821536b38d6bdb517db554d41cebfe5947ab7")
    #version("0.1.67", sha256="d3a88a1c3db0fab891e652f1eefa82aa846ae686927cd8ff0c53f6f10d245f99")
    #version("0.1.66", sha256="b77ee47da8a1b3d6fd03e23a8f853a2a666037f03e21546b4eb2b4cf43e13a96")
    #version("0.1.65", sha256="65cbe5a600c32569bb0b9f597ea318cc298a13b42d5fc98168c97bb11f320eae")
    #version("0.1.64", sha256="7fa89e90876fb5377efc54f3f37326a6fb83ec9e1326565819a75a4e80949886")
    #version("0.1.63", sha256="6abde084d6932b4e733df109c1e819a9f7f5ed8e68372a78821c0f3e76a20469")
    #version("0.1.62", sha256="d0e88dae5d983e500700f9f1636eaa742f9e673b4a230d7126f1380e021f373f")
    #version("0.1.61", sha256="0bedf96e8347b48740cfd3bfd2138649dcca76f634dc4038e2fd06dd773b20d1")
    #version("0.1.60", sha256="88da8f1978982101b8dbb144fd29ee362e4e8c97fc595c4992d555f80ce62a79")
    #version("0.1.59", sha256="16826e28f6282004932fde816b8b2677e89d2ad0e98a1a7f527f87596a3d4803")
    #version("0.1.58", sha256="899bcf2fad09d78a886dc4a9ee70dba7dc9c1fb5a1d7d38f164a97046b5434d9")
    #version("0.1.57", sha256="e5886548394f01dcfffb24c353d0b3f56410587756881c3cc43a4d6a831c98c5")
    #version("0.1.56", sha256="5f8f7bc056cb15bc0d45fedfe1ec38029d6f361aa2fb155a218a577a6d953013")
    #version("0.1.55", sha256="ccdcceb507223d25b121d4cb15e94339948cfb9bbe08be77e972db0d74fc5485")
    version("0.1.54", sha256="e1a9dcb0be7c828f752375409537d4b39c658dd6c6a0873fe21a24a556ec0e2a")

    patch("setup_v0.1.71.patch", when="@0.1.71")

    depends_on("cxx", type="build")  # generated

    # .bazelversion
    depends_on("bazel@6.4.0", type="build")

    with default_args(type="build"):
        depends_on("py-setuptools@30.3:")
        depends_on("py-setuptools@64:", when="@0.1.71:")
        depends_on("py-setuptools-scm")
        depends_on("py-setuptools-scm@8.1.0:", when="@0.1.71:")

    with default_args(type=("build", "run")):
        depends_on("python@3.9:")
        depends_on("py-numpy@1.16:")
        depends_on("py-numpy@1.22:", when="@0.1.71:")
        depends_on("py-ml-dtypes@0.3.1:")

    def patch(self):
        # Trick bazelisk into using the Spack-installed copy of bazel
        symlink(bazel.path, join_path("tools", "bazel"))

