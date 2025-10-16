# Copyright Spack Project Developers. See COPYRIGHT file for details.
#
# SPDX-License-Identifier: (Apache-2.0 OR MIT)

from spack_repo.builtin.build_systems.python import PythonPackage
from spack_repo.builtin.build_systems import python as pybs

from spack.package import *
import os

class PyVllm(PythonPackage):

    homepage = "https://docs.vllm.ai"
    url = "https://github.com/vllm-project/vllm/archive/refs/tags/v0.11.0.tar.gz"
    git = "https://github.com/vllm-project/vllm.git"

    license("Apache")

    version("main", branch="main")
    #version("0.11.0", sha256="607fa2777029215b3b659f7d94390ead42e6aa67f234f8f3b6cd5c222afdc905")
    version("0.11.0", commit="b8b302cde434df8c9289a2b465406b47ebab1c2d")

    depends_on("c",   type="build")
    depends_on("cxx", type="build")
    
    with default_args(type="build"):
        depends_on("py-build")
        depends_on("ninja")
        depends_on("py-packaging@24.2:")
        depends_on("py-setuptools-scm@8:")
        depends_on("py-wheel")
        depends_on("py-jinja2@3.1.6:")
        depends_on("py-regex")

    with default_args(type=("build", "link", "run")):
        depends_on("python@3.12:")
        depends_on("py-torch@2.8.0")
        depends_on("py-torchaudio")
        depends_on("py-torchvision")
        depends_on("py-triton")
        depends_on("cutlass")


class PythonPipBuilder(pybs.PythonPipBuilder):
    
    def install(self, pkg: PythonPackage, spec: Spec, prefix: Prefix) -> None:

        env_map = os.environ.copy()

        cutlass = self.pkg.spec["cutlass"].prefix
        env_map["VLLM_CUTLASS_SRC_DIR"] = cutlass
        
        env_map["MAX_JOBS"] = str(make_jobs)

        repo_root = self.pkg.stage.source_path

        with working_dir(repo_root):
            pp = spec["python"].command
            pp("use_existing_torch.py")

        pip = spec["python"].command
        pip.add_default_arg("-m", "pip")

        args = type(self).std_args(pkg) + [f"--prefix={prefix}"]

        for setting in pybs._flatten_dict(self.config_settings(spec, prefix)):
            args.append(f"--config-settings={setting}")
        for option in self.install_options(spec, prefix):
            args.append(f"--install-option={option}")
        for option in self.global_options(spec, prefix):
            args.append(f"--global-option={option}")

        if pkg.stage.archive_file and pkg.stage.archive_file.endswith(".whl"):
            args.append(pkg.stage.archive_file)
        else:
            args.append(".")

        with working_dir(self.build_directory):
            pip(*args, env=env_map)

    @property
    def build_directory(self):
        return "." 
