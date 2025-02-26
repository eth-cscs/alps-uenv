# Copyright Spack Project Developers. See COPYRIGHT file for details.
#
# SPDX-License-Identifier: (Apache-2.0 OR MIT)

import os

from spack.package import *


class Vmd(MakefilePackage, CudaPackage):
    """VMD provides user-editable materials which can be applied
    to molecular geometry.

    These material properties control the details of how VMD shades
    the molecular geometry, and how transparent or opaque the displayed
    molecular geometry is. With this feature, one can easily create nice
    looking transparent surfaces which allow inner structural details to
    be seen within a large molecular structure. The material controls can
    be particularly helpful when rendering molecular scenes using external
    ray tracers, each of which typically differ slightly.
    """

    homepage = "https://www.ks.uiuc.edu/Research/vmd/"
    version(
        "1.9.4a57",
        sha256="de278d0c5d969336d89068e0806fb50aaa0cb0f546ba985d840b279357860679",
    )

    url = "file://{0}/vmd-1.9.4a57.src.tar.gz".format(os.getcwd())
    manual_download = True
    redistribute(source=False, binary=False)

    requires("%gcc", msg="Currently GCC is hard-coded.")
    requires("target=aarch64", msg="Currently LINUXARM64 is hard-coded.")

    depends_on("tk@8.5")
    depends_on("tcl@8.5")
    depends_on("fltk")

    depends_on("libx11", type=("run", "link"))
    depends_on("gl@3:", type=("run", "link"))

    depends_on("patchelf", type="build")
    depends_on("gmake", type="build")

    patch(
        "configure-cuda.patch",
        sha256="a1954e289c80f520aaf9086b6fa41de64d78cc8d895ef7c54fb3e8c509da7fdf",
        working_dir="vmd-1.9.4a57",
    )

    def setup_build_environment(self, env):
        env.set("VMDINSTALLBINDIR", self.prefix.bin)
        env.set("VMDINSTALLLIBRARYDIR", self.prefix.lib64)
        env.set("PLUGINDIR", self.prefix.lib64.plugins)

    def build(self, spec, prefix):
        with working_dir(join_path(self.stage.source_path, "plugins")):
            gmake = Executable("gmake")
            gmake("LINUXARM64")
            gmake("distrib")

        VMD_SOURCE_DIR = join_path(self.stage.source_path, "vmd-1.9.4a57")
        with working_dir(VMD_SOURCE_DIR):
            os.symlink(join_path(self.prefix.lib64, "plugins"), "plugins")

            configure_opts = [
                "LINUXARM64",
                "GCC",
                "TCL",
                "FLTK",
                "FLTKOPENGL",
                "EGLPBUFFER",
                "PTHREADS",
                "SHARED",
                "NOSTATICPLUGINS",
                "LIBPNG",
                "ZLIB",
            ]

            if "+cuda" in spec:
                configure_opts.append("CUDA")

            configure(*configure_opts)

        with working_dir(join_path(VMD_SOURCE_DIR, "src")):
            make()

    def install(self, spec, prefix):
        with working_dir(join_path(self.stage.source_path, "vmd-1.9.4a57/src")):
            make("install")
            os.symlink(
                join_path(prefix.lib64, "vmd.so"),
                join_path(prefix.lib64, "vmd_LINUXARM64"),
            )

    # @run_after("install")
    # def ensure_rpaths(self):
    #     # make sure the executable finds and uses the Spack-provided
    #     # libraries, otherwise the executable may or may not run depending
    #     # on what is installed on the host
    #     patchelf = which("patchelf")
    #     rpath = ":".join(
    #         self.spec[dep].libs.directories[0]
    #         for dep in [
    #             "libx11",
    #             "libxi",
    #             "libxinerama",
    #             "gl",
    #             "fltk",
    #             "tcl",
    #             "tk",
    #             "cuda",
    #         ]
    #     )
    #     patchelf(
    #         "--set-rpath", rpath, join_path(self.prefix, "lib64", "vmd_LINUXAMD64")
    #     )

    def setup_run_environment(self, env):
        env.set("PLUGINDIR", self.spec.prefix.lib64.plugins)
