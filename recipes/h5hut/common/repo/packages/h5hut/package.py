# Copyright Spack Project Developers. See COPYRIGHT file for details.
#
# SPDX-License-Identifier: (Apache-2.0 OR MIT)


from spack_repo.builtin.build_systems.autotools import AutotoolsPackage

from spack.package import *


class H5hut(AutotoolsPackage):
    """H5hut (HDF5 Utility Toolkit).
    High-Performance I/O Library for Particle-based Simulations."""

    homepage = "https://amas.psi.ch/H5hut/"
    url = "https://amas.web.psi.ch/Downloads/H5hut/H5hut-0.0.0.tar.gz"
    git = "https://github.com/eth-cscs/h5hut.git"

    maintainers("biddisco")

    version("3a9e6d8",
            sha256="3b49cfd618a8aae4cd443908782a4a2681e2d5e0a5d99038822e98be84e1b3b5",
            url="https://jfrog.svc.cscs.ch/artifactory/cscs-reframe-tests/sphexa/h5hut_3a9e6d8.tgz"
    )
    version("2.0.0rc7", sha256="bc058c4817c356b7b7acfe386c586923103b90bdfa83575db3a91754767e6fab")
    version("master", branch="master")

    variant("fortran", default=True, description="Enable Fortran support")
    variant("mpi", default=True, description="Enable MPI support")

    depends_on("c", type="build")  # generated
    depends_on("cxx", type="build")  # generated
    depends_on("fortran", type="build")  # generated

    depends_on("autoconf", type="build", when="build_system=autotools")
    depends_on("automake", type="build", when="build_system=autotools")
    depends_on("libtool", type="build", when="build_system=autotools")

    depends_on("mpi", when="+mpi")
    # h5hut +mpi uses the obsolete function H5Pset_fapl_mpiposix:
    depends_on("hdf5@1.8:+mpi", when="+mpi")
    depends_on("hdf5@1.8:", when="~mpi")

    # If built in parallel, the following error message occurs:
    # install: .libs/libH5hut.a: No such file or directory
    parallel = False

    def flag_handler(self, name, flags):
        build_system_flags = []
        if (
            name == "cflags"
            and self.spec.satisfies("@:1")
            and self.spec["hdf5"].satisfies("@1.12:")
        ):
            build_system_flags = ["-DH5_USE_110_API"]
        return flags, None, build_system_flags

    def autoreconf(self, spec, prefix):
        which("bash")("autogen.sh")

    def configure_args(self):
        spec = self.spec
        config_args = ["--enable-shared"]
        config_args.append(f"--with-hdf5={spec['hdf5'].prefix}")

        if spec.satisfies("+fortran"):
            config_args.append("--enable-fortran")

        if spec.satisfies("+mpi"):
            config_args.extend(
                [
                    "--enable-large-indices",
                    "--enable-parallel",
                    "CC={0}".format(spec["mpi"].mpicc),
                    "CXX={0}".format(spec["mpi"].mpicxx),
                ]
            )

            if spec.satisfies("+fortran"):
                config_args.append("FC={0}".format(spec["mpi"].mpifc))

        return config_args
