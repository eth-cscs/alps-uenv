# Copyright Spack Project Developers. See COPYRIGHT file for details.
#
# SPDX-License-Identifier: (Apache-2.0 OR MIT)

from spack_repo.builtin.build_systems.cmake import CMakePackage, generator

from spack.package import *


class Dynolog(CMakePackage):
    """A performance monitoring daemon for heterogeneous CPU-GPU systems"""

    homepage = "https://github.com/facebookincubator/dynolog"
    url = "https://github.com/facebookincubator/dynolog/archive/refs/tags/v0.3.2.tar.gz"
    git = "https://github.com/facebookincubator/dynolog.git"
    
    license("MIT")

    version("main", branch="main", submodules=True)
    version("0.5.0", commit="7e967d1862bc405257f7bf3428ab2f74b33f5c2a", submodules=True)
    #version("0.3.2-dev", commit="7570766213484a926908c884888cfb701577a9cb", submodules=True)
    
    patch("cmake_fix.patch", level=1)
    
    depends_on("c", type="build")
    depends_on("cxx", type="build")
    
    generator("ninja")
    
    variant("use-prometheus", default=True, description="Enable logging to Prometheus")
    variant("with-unwind", default=True, description="Enable libunwind support")
    variant("with-gflags", default=False, description="Use gflags")
    
    depends_on("python")
    depends_on("rust")
    depends_on("prometheus-cpp", when="+use-prometheus")
    depends_on("libunwind", when="+with-unwind")
    #depends_on("gflags", when="+with-gflags")
    #depends_on("fmt")
    #depends_on("nlohmann-json")
    #depends_on("googletest")
    #depends_on("glog")
    
    def cmake_args(self):
        args = [
            self.define_from_variant("USE_PROMETHEUS", "use-prometheus"),
            self.define_from_variant("WITH_UNWIND", "with-unwind"),
            self.define_from_variant("WITH_GFLAGS", "with-gflags"),
        ]
        return args
    
    @run_after("install")
    def install_binaries(self):
        with working_dir(self.build_directory):
            mkdirp(self.prefix.bin)
            install("dynolog/src/dynolog", self.prefix.bin)
            install("release/dyno", self.prefix.bin)
    
