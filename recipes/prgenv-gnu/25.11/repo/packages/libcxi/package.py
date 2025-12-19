# This custom package definition effectively backports
# https://github.com/spack/spack-packages/pull/2288 to avoid having to bump the
# spack-packages commit.
# 
# This makes sure that autoconf etc. are dependencies for a build from git,
# even if the version is specified e.g. as 13.0.0, and not only for main.
#
# The next version of prgenv-gnu should bump the spack-packages commit and
# remove this definition.
from spack_repo.builtin.packages.libcxi.package import Libcxi as BuiltinLibcxi

from spack.package import *

class Libcxi(BuiltinLibcxi):
    with default_args(type="build"):
        depends_on("autoconf")
        depends_on("automake")
        depends_on("libtool")
        depends_on("pkgconfig")

    def autoreconf(self, spec, prefix):
        sh = which("sh")
        sh("autogen.sh")
