
# Copyright 2013-2024 Lawrence Livermore National Security, LLC and other
# Spack Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: (Apache-2.0 OR MIT)


from spack.package import *


class Deepmd(PythonPackage, CudaPackage, ROCmPackage):
    """DeePMD-kit is a package written in Python/C++, designed to minimize the effort required to build deep learning-based models of interatomic potential energy and force field and to perform molecular dynamics (MD)"""

    homepage = "https://docs.deepmodeling.com/projects/deepmd/en/stable/index.html#"
    git = "https://github.com/deepmodeling/deepmd-kit.git"
    url = "https://github.com/deepmodeling/deepmd-kit/archive/refs/tags/v2.2.11.tar.gz"
    license("GNU-LGPL")
    maintainers("mtaillefumier")

    version("3.0.0b0", sha256="44e5a6255f7890f4b9f1cc5e1525380c1d1e41dd75ac9e738d5b81a728759bba")
    version("3.0.0a0", sha256="36e9dc1b18313139b1e9482e06ec214e15a87ee74f5f9d565b8719998e088920")
    version("2.2.11", sha256="d22893a08c2556c5cb29682378105849cf672545c91ee52b10a97da6e9075ac3")
    version("2.2.10", sha256="c31ba1c8a3e874edbbaddc8ec61725a1b74734acb45578f820ab294835d12638")
    version("2.2.9", sha256="b14419367905b6dd938b9c54f91977c59c25da905a34a7b42585af4805fc4077")
    version("2.2.8", sha256="21c1e4a38caa81316df574af51f56aa2428dab7b0d71130250e407b81db80f29")
    version("2.2.7", sha256="25be126de336630493732b09d3b779b89cc916345b22dfb869cc4f3a3ba6dcde")
    version("2.2.6", sha256="3a4c61d9977b85d1600085dde67d3950f255ea2fcf12e9139d4d369167fce563")
    version("2.2.5", sha256="1b019f8fbd6d787bd0c03ef0f8160bfd7b6467f2646db5e3bda9153acf8ae878")
    version("2.2.4", sha256="e39ae25f1545b1cbd84b6122d97278414bbef08e1193a84f827ecdc748b8580b")

    variant(
        "tensorflow", default=True, description="Enable tensorflow support (original ML backend)"
    )
    variant("pytorch", default=False, description="Enable pytorch support (starting v3.0.0)")
    variant("cuda", default=False, description="Enable cuda support")
    variant("rocm", default=False, description="Enable rocm support")
    variant("lmp", default=False, description="Enable lammps plugins")
    variant("gromacs", default=False, description="Enable gromacs plugins")
    variant("horovod", default=False, description="Enable horovod support")

    # Historical dependencies
    depends_on("py-setuptools", type="build")
    depends_on("py-tensorflow@2.16:", when="+tensorflow")
    depends_on("py-tensorflow+mpi", when="+tensorflow")
    depends_on("py-torch", when="+pytorch")
    depends_on("py-mpi4py", when="+horovod")
    depends_on("py-ase")
    depends_on("py-scipy")
    depends_on("py-numpy")
    depends_on("py-pyyaml")
    depends_on("py-args")
    depends_on("py-python-hostlist@1.21:")
    depends_on("py-typing-extensions", when="python@:3.8")
    depends_on("py-importlib-metadata", when="python@:3.8")
    depends_on("py-sphinx-argparse")
    depends_on("py-pygments")
    depends_on("py-sphinxcontrib-bibtex")
    depends_on("py-scikit-build-core")
    depends_on("py-setuptools-scm")
    depends_on("py-scikit-build")
    depends_on("py-hatch-fancy-pypi-readme")
    # build lammps with plugin support
    depends_on("lammps+plugin", when="+lmp")

    # horovod needs some special settings
    depends_on("py-horovod controllers=mpi", when="+horovod")
    depends_on("py-horovod frameworks=tensorflow", when="+tensorflow+horovod")
    depends_on("py-horovod frameworks=pytorch", when="+pytorch+horovod")

    with when("+cuda"):
        depends_on("nccl")
        depends_on("py-horovod+cuda tensor_ops=nccl", when="+horovod")
        depends_on("py-tensorflow+cuda+nccl+mpi", when="+tensorflow")
        depends_on("py-torch+cuda", when="+pytorch")
        depends_on("lammps+cuda", when="+lmp")
    with when("+rocm"):
        depends_on("rccl")
        depends_on("py-horovod+rocm", when="+horovod")
        depends_on("py-tensorflow@2.16:+rocm", when="+tensorflow")
        depends_on("py-torch+rocm", when="+pytorch")
        depends_on("lammps+rocm", when="+lmp")

    def setup_build_environment(self, env):
        if "+cuda" in self.spec:
            env.set("DP_VARIANT", "cuda")
            env.set("CMAKE_ARGS", "-DUSE_CUDA_TOOLKIT=ON")
        if "+rocm" in self.spec:
            env.set("DP_VARIANT", "rocm")
