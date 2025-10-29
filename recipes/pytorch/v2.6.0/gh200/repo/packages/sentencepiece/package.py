# Copyright 2013-2024 Lawrence Livermore National Security, LLC and other
# Spack Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: (Apache-2.0 OR MIT)


from spack.package import *


class Sentencepiece(CMakePackage):
    """Unsupervised text tokenizer for Neural Network-based text generation.

    This is the C++ package."""

    homepage = "https://github.com/google/sentencepiece"
    url = "https://github.com/google/sentencepiece/archive/v0.1.85.tar.gz"

    maintainers("adamjstewart")

    license("Apache-2.0")

    version("0.1.99", sha256="63617eaf56c7a3857597dcd8780461f57dd21381b56a27716ef7d7e02e14ced4")
    version("0.1.91", sha256="acbc7ea12713cd2a8d64892f8d2033c7fd2bb4faecab39452496120ace9a4b1b")
    version("0.1.85", sha256="dd4956287a1b6af3cbdbbd499b7227a859a4e3f41c9882de5e6bdd929e219ae6")

    variant("with-TCMalloc", default=False, description="Enable TCMalloc if available")
    variant("with-TCMalloc-static", default=False, description="Link static library of TCMALLOC")
    variant("no-tl", default=False, description="Disable thread_local operator")

    depends_on("cxx", type="build")  # generated

    depends_on("cmake@3.1:", type="build")
    depends_on("gperftools", when="+with-TCMalloc")  # optional, 10-40% performance improvement

    def cmake_args(self):
        args = [
            self.define_from_variant("SPM_ENABLE_TCMALLOC", "with-TCMalloc"),
            self.define_from_variant("SPM_TCMALLOC_STATIC", "with-TCMalloc-static"),
            self.define_from_variant("SPM_NO_THREADLOCAL", "no-tl"),
        ]
        return args
