# Copyright Spack Project Developers. See COPYRIGHT file for details.
#
# SPDX-License-Identifier: (Apache-2.0 OR MIT)

from spack.build_systems import cmake, meson
from spack.package import *


class Dftd4(MesonPackage, CMakePackage):
    """Generally Applicable Atomic-Charge Dependent London Dispersion Correction"""

    homepage = "https://www.chemie.uni-bonn.de/pctc/mulliken-center/software/dftd4"
    url = "https://github.com/dftd4/dftd4/releases/download/v0.0.0/dftd4-0.0.0.tar.xz"
    git = "https://github.com/dftd4/dftd4.git"

    maintainers("awvwgk")

    license("LGPL-3.0-only")

    build_system("cmake", "meson", default="meson")

    version("main", branch="main")
    version("3.7.0", sha256="4e8749df6852bf863d5d1831780a2d30e9ac4afcfebbbfe5f6a6a73d06d6c6ee")
    version("3.6.0", sha256="56b3b4650853a34347d3d56c93d7596ecbe2208c4a14dbd027959fd4a009679d")
    version("3.5.0", sha256="d2bab992b5ef999fd13fec8eb1da9e9e8d94b8727a2e624d176086197a00a46f")
    version("3.4.0", sha256="24fcb225cdd5c292ac26f7d3204ee3c4024174adb5272eeda9ae7bc57113ec8d")
    version("3.3.0", sha256="408720b8545532d5240dd743c05d57b140af983192dad6d965b0d79393d0a9ef")
    version("3.2.0", sha256="cef505e091469aa9b8f008ee1756545bb87b02760bb2c7ca54854e20ba8c590a")
    version("3.1.0", sha256="b652aa7cbf8d087c91bcf80f2d5801459ecf89c5d4176ebb39e963ee740ed54b")
    version("3.0.0", sha256="a7539d68d48d851bf37b79e37ea907c9da5eee908d0aa58a0a7dc15f04f8bc35")

    depends_on("c", type="build")
    depends_on("fortran", type="build")

    variant("openmp", default=True, description="Use OpenMP parallelisation")
    variant(
        "python",
        default=False,
        when="build_system=meson",
        description="Build Python extension module",
    )

    depends_on("meson@0.57.1:", type="build", when="build_system=meson")  # mesonbuild/meson#8377

    depends_on("blas")
    depends_on("lapack")
    depends_on("pkgconfig", type="build")

    depends_on("py-cffi", when="+python")
    depends_on("python@3.6:", when="+python")

    for build_system in ["cmake", "meson"]:
        depends_on(f"mctc-lib build_system={build_system}", when=f"build_system={build_system}")
        depends_on(f"multicharge build_system={build_system}", when=f"build_system={build_system}")

    extends("python", when="+python")

    def url_for_version(self, version):
        if version <= Version("3.6.0"):
            return f"https://github.com/dftd4/dftd4/releases/download/v{version}/dftd4-{version}-source.tar.xz"
        return super().url_for_version(version)


class MesonBuilder(meson.MesonBuilder):
    def meson_args(self):
        lapack = self.spec["lapack"].libs.names[0]
        if lapack == "lapack":
            lapack = "netlib"
        elif lapack.startswith("mkl"):
            lapack = "mkl"
        elif lapack != "openblas":
            lapack = "auto"

        return [
            "-Dlapack={0}".format(lapack),
            "-Dopenmp={0}".format(str("+openmp" in self.spec).lower()),
            "-Dpython={0}".format(str("+python" in self.spec).lower()),
        ]


class CMakeBuilder(cmake.CMakeBuilder):
    def cmake_args(self):
        return [self.define_from_variant("WITH_OPENMP", "openmp")]
