# Copyright 2013-2023 Lawrence Livermore National Security, LLC and other
# Spack Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: (Apache-2.0 OR MIT)

import os
import sys

from spack.package import *


class Vasp(CMakePackage, CudaPackage):
    """
    The Vienna Ab initio Simulation Package (VASP)
    is a computer program for atomic scale materials modelling,
    e.g. electronic structure calculations
    and quantum-mechanical molecular dynamics, from first principles.
    """

    homepage = "https://vasp.at"
    url = "file://{0}/vasp-6.1.0.tar.bz2".format(os.getcwd())
    manual_download = True

    generator("ninja")

    version("6.4.3", sha256="348987f550541d40135c3b8a177db9e69b7477b9e2ad53a93022e8213890e2ec")
    version("6.4.2", sha256="a4e3e6e83ae5b2277cde634a30919a379d102ee3294dd8ea33c388bb52c17077")
    version("6.4.1", sha256="d4d82577f29b2f5116b27a4e554e6d4bfc4525f2579307e00933e8600309344f")
    version("6.4.0", sha256="b27b39d99a81f5ef6f1efe3931ec00dcb1dbbd99f53e7f927952c43fa0a8d826")
    version("6.3.0", sha256="5c89e96ca485d64a3050ffcaa2833eda318a66dae9408a7217dd6af0e61bc813")
    version("6.2.1", sha256="7ea7e0467af7b7550ee6d15b6b27a2ab7978c71a3b0575bc895f8135fabd55ca")
    version("6.2.0", sha256="4ce132d588d518abac749522735ccffa72b0ae2be18fd866595628c4962a7e2d")
    version("6.1.0", sha256="c50eb1bfb21ea5ac9cacf459b9b09c818365e6eb0390e4926eda521921c06c75")

    resource(
        name="cmake_repo",
        git="https://github.com/AdhocMan/vasp_cmake.git",
        commit="58d0dc31bbe920e84b7650e687491faff73c86a7",
    )

    variant("profiling", default=False, description="Enable profiling")
    variant("collective", default=True, description="Enable collective MPI calls")
    variant("inplace", default=True, description="Enable MPI inplace")
    variant("avoidalloc", default=False, description="Enable avoidance of automatic allocations")
    variant("vasp6", default=True, when="@6:", description="Enable VASP 6.x features")
    variant("tbdyn", default=True, description="Enable advanced molecular dynamics")
    variant("bse", default=True, description="Enable bse_te")
    variant("fock_dblbuf", default=False, description="Enable double buffering for exchange potential")
    variant("shmem", default=False, description="Enable shared memory for reduced memory usage")
    variant("shmem_bcast", default=False, description="")
    variant("shmem_rproj", default=False, description="")
    variant("sysv", default=False, description="")
    variant("openmp", default=True, description="")
    variant("fftlib", when="+openmp", default=False, description="")
    variant("scalapack", default=False, description="")
    variant("hdf5", default=False, description="")
    variant("wannier90", default=False, description="")
    variant("libxc", default=False, description="")
    variant("ncclp2p", when="+cuda", default=True, description="")
    variant("cusolvermp", when="+cuda", default=False, description="")


    with when("+openmp"):
        conflicts("^fftw~openmp")
        conflicts("^amdfftw~openmp")
        conflicts("^amdblis threads=none")
        conflicts("^amdblis threads=pthreads")
        conflicts("^openblas threads=none")
        conflicts("^openblas threads=pthreads")

    requires(
        "%nvhpc",
        when="+cuda",
        msg="NVHPC compiler is required for CUDA support"
    )

    depends_on("ninja", type="build")
    depends_on("blas")
    depends_on("lapack")
    depends_on("fftw-api@3:")
    depends_on("fftw-api@3:+openmp", when="+openmp")
    depends_on("mpi", type=("build", "link", "run"))
    depends_on("scalapack", when="+scalapack")
    depends_on("hdf5+fortran", when="+hdf5")
    depends_on("libxc~cuda~fhc", when="+libxc")
    depends_on("wannier90", when="+wannier90")

    conflicts(
        "%gcc@:8", msg="GFortran before 9.x does not support all features needed to build VASP"
    )

    patch("mpix_cuda.patch")

    @run_before("cmake")
    def copy_cmake(self):
        copy_tree("vasp_cmake", ".")

    def cmake_args(self):
        spec = self.spec

        args = [
            self.define_from_variant("VASP_PROFILING", "profiling"),
            self.define_from_variant("VASP_COLLECTIVE", "collective"),
            self.define_from_variant("VASP_MPI_INPLACE", "inplace"),
            self.define_from_variant("VASP_AVOIDALLOC", "avoidalloc"),
            self.define_from_variant("VASP_VASP6", "vasp6"),
            self.define_from_variant("VASP_TBDYN", "tbdyn"),
            self.define_from_variant("VASP_FOCK_DBLBUF", "fock_dblbuf"),
            self.define_from_variant("VASP_SHMEM", "shmem"),
            self.define_from_variant("VASP_SHMEM_BCAST", "shmem_bcast"),
            self.define_from_variant("VASP_SHMEM_RPROJ", "shmem_rproj"),
            self.define_from_variant("VASP_SYSV", "sysv"),
            self.define_from_variant("VASP_OPENMP", "openmp"),
            self.define_from_variant("VASP_FFTLIB", "fftlib"),
            self.define_from_variant("VASP_SCALAPACK", "scalapack"),
            self.define_from_variant("VASP_HDF5", "hdf5"),
            self.define_from_variant("VASP_WANNIER90", "wannier90"),
            self.define_from_variant("VASP_LIBXC", "libxc"),
            self.define_from_variant("VASP_CUDA", "cuda"),
            self.define_from_variant("VASP_BSE", "bse"),
            self.define_from_variant("VASP_NCCLP2P", "ncclp2p"),
            self.define("BLAS_LIBRARIES", spec["blas"].libs.joined(";")),
            self.define("LAPACK_LIBRARIES", spec["lapack"].libs.joined(";")),
            "-DVASP_LIBBEEF=OFF",
            "-DVASP_DFTD4=OFF",
        ]

        if not spec.satisfies("^[virtuals=fftw-api] fftw"):
            args += [
                self.define("FFTW_SERIAL_LIBRARIES", spec["fftw-api"].libs.joined(";")),
                self.define("FFTW_SERIAL_INCLUDE_DIRS", spec["fftw-api"].prefix.include),
                self.define("FFTW_OMP_LIBRARIES", spec["fftw-api"].libs.joined(";")),
                self.define("FFTW_OMP_INCLUDE_DIRS", spec["fftw-api"].prefix.include),
            ]

        if spec.satisfies("%nvhpc +openmp"):
            args += [
                self.define("OpenMP_-mp_LIBRARY", "-mp"),
                self.define("OpenMP_Fortran_FLAGS", "-mp"),
                self.define("OpenMP_C_FLAGS", "-mp"),
                self.define("OpenMP_CXX_FLAGS", "-mp"),
                self.define("OpenMP_Fortran_LIB_NAMES", "-mp"),
                self.define("OpenMP_C_LIB_NAMES", "-mp"),
                self.define("OpenMP_CXX_LIB_NAMES", "-mp"),
            ]


        if spec.satisfies("+cuda"):
            cuda_arch = self.spec.variants["cuda_arch"].value
            if cuda_arch[0] != "none":
                args += [self.define("CMAKE_CUDA_ARCHITECTURES", cuda_arch)]
            nvhpc_root = os.path.dirname(os.path.dirname(self.compiler.fc))
            args += [self.define("QD_ROOT", join_path(nvhpc_root, "extras"))]
            args += [self.define("VASP_CUDA_VERSION",spec["cuda"].version.up_to(2))]

        return args
