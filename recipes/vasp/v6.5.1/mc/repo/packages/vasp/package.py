# Copyright Spack Project Developers. See COPYRIGHT file for details.
#
# SPDX-License-Identifier: (Apache-2.0 OR MIT)

import os
from pathlib import Path

from spack.package import *


class Vasp(MakefilePackage, CudaPackage):
    """
    The Vienna Ab initio Simulation Package (VASP)
    is a computer program for atomic scale materials modelling,
    e.g. electronic structure calculations
    and quantum-mechanical molecular dynamics, from first principles.
    """

    homepage = "https://vasp.at"
    url = "file://{0}/vasp-6.1.0.tar.bz2".format(os.getcwd())
    manual_download = True

    version("6.5.1", sha256="1db264b3deed97dec3a535e892f0b9215e51ae3e2870ec9d50c56b9f5c3ca2c2")
    version("6.5.0", sha256="805ea6fbc41e2eac32a941d36e4981691bc098bfa445f0386b3b06aaf1f0f566")
    version("6.4.3", sha256="348987f550541d40135c3b8a177db9e69b7477b9e2ad53a93022e8213890e2ec")
    version("6.4.2", sha256="a4e3e6e83ae5b2277cde634a30919a379d102ee3294dd8ea33c388bb52c17077")
    version("6.4.1", sha256="d4d82577f29b2f5116b27a4e554e6d4bfc4525f2579307e00933e8600309344f")
    version("6.4.0", sha256="b27b39d99a81f5ef6f1efe3931ec00dcb1dbbd99f53e7f927952c43fa0a8d826")
    version("6.3.0", sha256="5c89e96ca485d64a3050ffcaa2833eda318a66dae9408a7217dd6af0e61bc813")
    version("6.2.1", sha256="7ea7e0467af7b7550ee6d15b6b27a2ab7978c71a3b0575bc895f8135fabd55ca")
    version("6.2.0", sha256="4ce132d588d518abac749522735ccffa72b0ae2be18fd866595628c4962a7e2d")
    version("6.1.0", sha256="c50eb1bfb21ea5ac9cacf459b9b09c818365e6eb0390e4926eda521921c06c75")

    variant("openmp", default=False, description="Enable openmp build")
    variant("cuda", default=False, description="Enables running on Nvidia GPUs")
    variant("hdf5", default=False, description="Enabled HDF5 support")
    variant("wannier90", default=False, description="Enabled Wannier90 support")

    # Language dependencies (required in Spack v1.0+)
    depends_on("c", type="build")
    depends_on("cxx", type="build")
    depends_on("fortran", type="build")

    #depends_on("rsync", type="build")
    depends_on("blas")
    depends_on("lapack")
    depends_on("fftw-api")
    depends_on("fftw+openmp", when="+openmp ^[virtuals=fftw-api] fftw")
    depends_on("amdfftw+openmp", when="+openmp ^[virtuals=fftw-api] amdfftw")
    depends_on("amdblis threads=openmp", when="+openmp ^[virtuals=blas] amdblis")
    depends_on("openblas threads=openmp", when="+openmp ^[virtuals=blas] openblas")
    depends_on("mpi", type=("build", "link", "run"))
    # fortran oddness requires the below
    depends_on("scalapack")

    # Use the bundled NCCL library of NVHPC instead.
    # The spack build nccl library leads to linking errors.
    #depends_on("nccl", when="+cuda")


    depends_on("hdf5+fortran+mpi", when="+hdf5")
    depends_on("wannier90", when="+wannier90")

    conflicts(
        "%gcc@:8", msg="GFortran before 9.x does not support all features needed to build VASP"
    )
    requires("%nvhpc", when="+cuda", msg="vasp requires nvhpc to build the openacc build")
    conflicts("cuda_arch=none", when="+cuda", msg="CUDA arch required when building openacc port")

    def edit(self, spec, prefix):
        llibs = list(self.compiler.stdcxx_libs)
        incs = [spec["fftw-api"].headers.include_flags]

        llibs.extend([spec["blas"].libs.ld_flags, spec["lapack"].libs.ld_flags])

        cpp_options = ["-DCRAY_MPICH"]

        fc = [spec["mpi"].mpifc]
        fcl = [spec["mpi"].mpifc]

        omp_flag = "-fopenmp"

        include_string = "makefile.include."

        # gcc
        if spec.satisfies("%gcc"):
            include_string += "gnu"
            if spec.satisfies("+openmp"):
                include_string += "_omp"
            make_include = join_path("arch", include_string)
        # nvhpc
        elif spec.satisfies("%nvhpc"):

            qd_root = join_path(
                Path(self.compiler.fc).parent.parent.absolute(),
                "extras",
                "qd",
            )

            incs.append(f"-I{join_path(qd_root, 'include', 'qd')}")
            llibs.extend([f"-L{join_path(qd_root, 'lib')}", "-lqdmod", "-lqd"])
            llibs.extend([f"-Wl,-rpath,{join_path(qd_root, 'lib')}"])

            include_string += "nvhpc"
            if spec.satisfies("+openmp"):
                include_string += "_omp"
            if spec.satisfies("+cuda"):
                include_string += "_acc"
            make_include = join_path("arch", include_string)
            omp_flag = "-mp"
            filter_file("= nvfortran", f"= {self.compiler.fc}", make_include)
            filter_file("which nvfortran", f"which {self.compiler.fc}", make_include)

        if spec.satisfies("+openmp"):
            cpp_options.extend(["-D_OPENMP"])
            llibs.extend([spec["fftw-api:openmp"].libs.ld_flags])
            fc.append(omp_flag)
            fcl.append(omp_flag)
        else:
            llibs.append(spec["fftw-api"].libs.ld_flags)

        llibs.append(spec["scalapack"].libs.ld_flags)

        if spec.satisfies("+cuda"):
            # openacc
            llibs.extend(["-cudalib=cublas,cusolver,cufft,nccl", "-cuda"])
            #incs.append(spec["nccl"].headers.include_flags)
            #llibs.append(spec["nccl"].libs.ld_flags)
            fc.append("-acc")
            fcl.append("-acc")
            cuda_flags = [f"cuda{str(spec['cuda'].version.dotted[0:2])}"]
            for f in spec.variants["cuda_arch"].value:
                cuda_flags.append(f"cc{f}")
            fc.append(f"-gpu={','.join(cuda_flags)}")
            fcl.append(f"-gpu={','.join(cuda_flags)}")
            fcl.extend(list(self.compiler.stdcxx_libs))
            cc = [spec["mpi"].mpicc, "-acc"]
            cc.append(f"-gpu={','.join(cuda_flags)}")
            if spec.satisfies("+openmp"):
                cc.append(omp_flag)
            filter_file("^CC[ \t]*=.*$", f"CC = {' '.join(cc)}", make_include)

        if spec.satisfies("+hdf5"):
            cpp_options.append("-DVASP_HDF5")
            llibs.append(spec["hdf5:fortran"].libs.ld_flags)
            incs.append(spec["hdf5"].headers.include_flags)

        if spec.satisfies("+wannier90"):
            cpp_options.append("-DVASP2WANNIER90")
            llibs.append(spec["wannier90"].libs.ld_flags)


        filter_file(r"^VASP_TARGET_CPU[ ]{0,}\?=.*", "", make_include)

        # prepend CPP options
        filter_file(
            "^CPP_OPTIONS[ \t]*=", f"CPP_OPTIONS = {' '.join(cpp_options)} ", make_include
        )
        filter_file(r"^INCS[ \t]*\+?=.*$", f"INCS = {' '.join(incs)}", make_include)
        filter_file(r"^LLIBS[ \t]*\+?=.*$", f"LLIBS = {' '.join(llibs)}", make_include)
        filter_file(r"^LLIBS[ \t]*\+=[ ]*-.*$", "", make_include)
        filter_file("^FC[ \t]*=.*$", f"FC = {' '.join(fc)}", make_include)
        filter_file("^FCL[ \t]*=.*$", f"FCL = {' '.join(fcl)}", make_include)

        os.rename(make_include, "makefile.include")


    def setup_build_environment(self, spack_env):
        if self.spec.satisfies("%nvhpc +cuda"):
            spack_env.set("NVHPC_CUDA_HOME", self.spec["cuda"].prefix)

    def build(self, spec, prefix):
        make("DEPS=1, all, -j1")

    def install(self, spec, prefix):
        install_tree("bin/", prefix.bin)
