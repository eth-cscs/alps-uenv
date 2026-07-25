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
        depends_on("cmake")
        depends_on("ninja")
        depends_on("py-packaging@24.2:")
        depends_on("py-setuptools-scm@8:")
        depends_on("py-wheel")
        depends_on("py-regex")
        depends_on("py-pybind11")

    with default_args(type=("build", "link", "run")):
        depends_on("py-jinja2@3.1.6:")
        depends_on("python@3.12:")
        depends_on("py-torch@2.8.0")
        depends_on("py-torchaudio")
        depends_on("py-torchvision")
        depends_on("py-triton")
        depends_on("cutlass")
        depends_on("py-cutlass")
        depends_on("cuda")
        depends_on("cudnn")
        depends_on("cusparselt")
        depends_on("cudss")

    patch("cmake_fix_8.patch", when="@0.11.0")


class PythonPipBuilder(pybs.PythonPipBuilder):
    
    #def install(self, pkg: PythonPackage, spec: Spec, prefix: Prefix) -> None:

    #    env_map = os.environ.copy()

    #    sp_py = spec["python"].command.path

    #    # Enable GPU backends explicitly
    #    cmake_args = [
    #        f"-DPython3_EXECUTABLE={sp_py}",
    #        "-DUSE_CUDNN=ON",
    #        "-DUSE_CUSPARSELT=ON",
    #        "-DUSE_CUDSS=ON",
    #        "-DUSE_CUFILE=ON",
    #    ]

    #    # CUDA & friends: give CMake a head start so it finds the right trees
    #    cuda   = spec["cuda"].prefix
    #    cudnn  = spec["cudnn"].prefix if "cudnn" in spec else None
    #    cuslt  = spec["cusparselt"].prefix if "cusparselt" in spec else None
    #    cudss  = spec["cudss"].prefix if "cudss" in spec else None

    #    cmake_args += [
    #        f"-DCUDAToolkit_ROOT={cuda}",
    #        f"-DCMAKE_PREFIX_PATH={';'.join(str(p) for p in [cuda, cudnn, cuslt, cudss] if p)}",
    #    ]

    #    # CUTLASS: vLLM expects the repo-ish tree; use prefix and let its CMake look for headers there
    #    cutlass = spec["cutlass"].prefix
    #    env_map["VLLM_CUTLASS_SRC_DIR"] = str(cutlass)

    #    # Parallelism hint (honored by many pyproject/cmake build backends)
    #    env_map["MAX_JOBS"] = str(make_jobs)


    #    #cutlass = self.pkg.spec["cutlass"].prefix
    #    #env_map["VLLM_CUTLASS_SRC_DIR"] = cutlass
    #    #
    #    #env_map["MAX_JOBS"] = str(make_jobs)

    #    #env_map["USE_CUDNN"] = "1"
    #    #env_map["USE_CUSPARSELT"] = "1"
    #    #env_map["USE_CUDSS"] = "1"
    #    #env_map["USE_CUFILE"] = "1"

    #    repo_root = self.pkg.stage.source_path

    #    with working_dir(repo_root):
    #        pp = spec["python"].command
    #        pp("use_existing_torch.py")

    #    # Thread our CMake options into the underlying build
    #    # Most projects (incl. vLLM) honor CMAKE_ARGS environment.
    #    # If vLLM also has VLLM_CMAKE_ARGS, you can set that too; CMAKE_ARGS is the generic one.
    #    extra = " ".join(cmake_args)
    #    env_map["CMAKE_ARGS"] = (extra if "CMAKE_ARGS" not in env_map else env_map["CMAKE_ARGS"] + " " + extra)

    #    # Safety: also set PYTHON to Spack’s python; some scripts check this var.
    #    env_map["PYTHON"] = sp_py

    #    pip = spec["python"].command
    #    pip.add_default_arg("-m", "pip")

    #    args = type(self).std_args(pkg) + [f"--prefix={prefix}"]

    #    for setting in pybs._flatten_dict(self.config_settings(spec, prefix)):
    #        args.append(f"--config-settings={setting}")
    #    for option in self.install_options(spec, prefix):
    #        args.append(f"--install-option={option}")
    #    for option in self.global_options(spec, prefix):
    #        args.append(f"--global-option={option}")

    #    if pkg.stage.archive_file and pkg.stage.archive_file.endswith(".whl"):
    #        args.append(pkg.stage.archive_file)
    #    else:
    #        args.append(".")

    #    with working_dir(self.build_directory):
    #        pip(*args, env=env_map)
    #def install(self, pkg: PythonPackage, spec: Spec, prefix: Prefix) -> None:
    #    env_map = os.environ.copy()

    #    # Make sure any 'python3' the build calls is Spack’s Python.
    #    sp_py_dir = os.path.join(spec["python"].prefix.bin)
    #    env_map["PATH"] = sp_py_dir + os.pathsep + env_map.get("PATH", "")

    #    sp_py = spec["python"].command.path

    #    # CUDA hints
    #    cuda   = spec["cuda"].prefix
    #    cudnn  = spec["cudnn"].prefix      if "cudnn"      in spec else None
    #    cuslt  = spec["cusparselt"].prefix if "cusparselt" in spec else None
    #    cudss  = spec["cudss"].prefix      if "cudss"      in spec else None

    #    # CUTLASS tree (vLLM expects a source-ish layout; prefix generally works)
    #    env_map["VLLM_CUTLASS_SRC_DIR"] = str(spec["cutlass"].prefix)

    #    # Parallelism
    #    env_map["MAX_JOBS"] = str(make_jobs)

    #    # CMake flags that vLLM will append after its own defaults
    #    cmake_args = [
    #        # Use the *same* Python throughout (find_package + custom var)
    #        f"-DPython3_EXECUTABLE={sp_py}",
    #        f"-DVLLM_PYTHON_EXECUTABLE={sp_py}",

    #        # Ensure CUDA toolkit and related packages are discoverable
    #        f"-DCUDAToolkit_ROOT={cuda}",
    #        f"-DCMAKE_PREFIX_PATH={';'.join(str(p) for p in [cuda, cudnn, cuslt, cudss] if p)}",

    #        # Feature toggles — force ON with explicit type so cache can’t “win”
    #        "-DUSE_CUDNN:BOOL=ON",
    #        "-DUSE_CUSPARSELT:BOOL=ON",
    #        "-DUSE_CUDSS:BOOL=ON",
    #        "-DUSE_CUFILE:BOOL=ON",
    #    ]

    #    # Thread into the build environment so setup.py picks them up
    #    extra = " ".join(cmake_args)
    #    env_map["CMAKE_ARGS"] = (extra if "CMAKE_ARGS" not in env_map
    #                             else env_map["CMAKE_ARGS"] + " " + extra)

    #    # Some parts check $PYTHON as well
    #    env_map["PYTHON"] = sp_py

    #    # vLLM has a helper that should run with Spack’s Python
    #    with working_dir(pkg.stage.source_path):
    #        spec["python"].command("use_existing_torch.py")

    #    # Normal pip install (Spack passes --no-build-isolation via std_args)
    #    pip = spec["python"].command
    #    pip.add_default_arg("-m", "pip")

    #    args = type(self).std_args(pkg) + [f"--prefix={prefix}"]
    #    for setting in pybs._flatten_dict(self.config_settings(spec, prefix)):
    #        args.append(f"--config-settings={setting}")
    #    for option in self.install_options(spec, prefix):
    #        args.append(f"--install-option={option}")
    #    for option in self.global_options(spec, prefix):
    #        args.append(f"--global-option={option}")

    #    if pkg.stage.archive_file and pkg.stage.archive_file.endswith(".whl"):
    #        args.append(pkg.stage.archive_file)
    #    else:
    #        args.append(".")

    #    with working_dir(self.build_directory):
    #        pip(*args, env=env_map)
    #def install(self, pkg: PythonPackage, spec: Spec, prefix: Prefix) -> None:
    #    env_map = os.environ.copy()

    #    # 1) Ensure any 'python3' resolves to Spack's python
    #    sp_py      = spec["python"].command.path
    #    sp_py_bind = str(spec["python"].prefix.bin)
    #    env_map["PATH"]   = sp_py_bind + os.pathsep + env_map.get("PATH", "")
    #    env_map["PYTHON"] = sp_py

    #    # 2) Feature toggles: vLLM's CMake reads these from the environment
    #    env_map["USE_CUDNN"]      = "1"
    #    env_map["USE_CUSPARSELT"] = "1"
    #    env_map["USE_CUDSS"]      = "1"
    #    env_map["USE_CUFILE"]     = "1"
    #    env_map["VLLM_USE_CUDNN"]      = "1"
    #    env_map["VLLM_USE_CUSPARSELT"] = "1"
    #    env_map["VLLM_USE_CUDSS"]      = "1"
    #    env_map["VLLM_USE_CUFILE"]     = "1"

    #    # 3) Build a solid PYTHONPATH for the generator to import from
    #    #    (Spack's build env already has PYTHONPATH for deps; we preserve & ensure it exists)
    #    py_env = env_map.get("PYTHONPATH", "")
    #    # Also compute the site-packages for Spack's python (so we can add it explicitly if needed)
    #    from sys import version_info as _vi
    #    pyver_short = f"{_vi.major}.{_vi.minor}"
    #    sp_py_site = os.path.join(str(spec["python"].prefix), "lib", f"python{pyver_short}", "site-packages")
    #    pp_parts = [p for p in (sp_py_site, py_env) if p]
    #    env_map["PYTHONPATH"]      = os.pathsep.join(pp_parts)
    #    env_map["VLLM_PYTHON_PATH"] = env_map["PYTHONPATH"]

    #    # 4) CUDA/CUTLASS
    #    cuda  = spec["cuda"].prefix
    #    cudnn = spec["cudnn"].prefix       if "cudnn"      in spec else None
    #    cuslt = spec["cusparselt"].prefix  if "cusparselt" in spec else None
    #    cudss = spec["cudss"].prefix       if "cudss"      in spec else None
    #    env_map["CUDA_HOME"] = str(cuda)  # some paths look at this var
    #    env_map["VLLM_CUTLASS_SRC_DIR"] = str(spec["cutlass"].prefix)
    #    env_map["MAX_JOBS"] = str(make_jobs)

    #    # 5) Strong CMake pins (and make the toggles sticky as cache values too)
    #    cmake_args = [
    #        f"-DPython3_EXECUTABLE={sp_py}",
    #        f"-DPython3_ROOT_DIR={spec['python'].prefix}",
    #        "-DPython3_FIND_STRATEGY=LOCATION",
    #        f"-DCUDAToolkit_ROOT={cuda}",
    #        f"-DCMAKE_CUDA_COMPILER={cuda}/bin/nvcc",
    #        f"-DCMAKE_PREFIX_PATH={';'.join(str(p) for p in [cuda, cudnn, cuslt, cudss] if p)}",
    #        # mirror the env toggles as cache values so CMake variables are ON even if code reads the cache
    #        "-DUSE_CUDNN:BOOL=ON",
    #        "-DUSE_CUSPARSELT:BOOL=ON",
    #        "-DUSE_CUDSS:BOOL=ON",
    #        "-DUSE_CUFILE:BOOL=ON",
    #        "-DVLLM_USE_CUDNN:BOOL=ON",
    #        "-DVLLM_USE_CUSPARSELT:BOOL=ON",
    #        "-DVLLM_USE_CUDSS:BOOL=ON",
    #        "-DVLLM_USE_CUFILE:BOOL=ON",
    #        "-DCMAKE_VERBOSE_MAKEFILE=ON",
    #    ]
    #    extra = " ".join(cmake_args)
    #    env_map["CMAKE_ARGS"] = (extra if "CMAKE_ARGS" not in env_map
    #                             else env_map["CMAKE_ARGS"] + " " + extra)

    #    # 6) Make sure helper script runs with Spack's Python
    #    with working_dir(pkg.stage.source_path):
    #        spec["python"].command("use_existing_torch.py")

    #    ## 7) Nuke stale CMake cache from previous tries (setuptools build dir)
    #    #try:
    #    #    import sysconfig, shutil as _shutil, pathlib
    #    #    plat = sysconfig.get_platform().replace("-", "_")
    #    #    btemp = pathlib.Path("build") / f"temp.{plat}"
    #    #    if btemp.exists():
    #    #        _shutil.rmtree(btemp)
    #    #except Exception:
    #    #    pass

    #    # 8) pip install (no build isolation; pass our env so setup.py sees everything)
    #    pip = spec["python"].command
    #    pip.add_default_arg("-m", "pip")
    #    args = type(self).std_args(pkg) + [f"--prefix={prefix}"]
    #    for setting in pybs._flatten_dict(self.config_settings(spec, prefix)):
    #        args.append(f"--config-settings={setting}")
    #    for option in self.install_options(spec, prefix):
    #        args.append(f"--install-option={option}")
    #    for option in self.global_options(spec, prefix):
    #        args.append(f"--global-option={option}")
    #    args.append(pkg.stage.archive_file if (pkg.stage.archive_file and pkg.stage.archive_file.endswith(".whl")) else ".")
    #    with working_dir(self.build_directory):
    #        pip(*args, env=env_map)
    def install(self, pkg: PythonPackage, spec: Spec, prefix: Prefix) -> None:
        import sysconfig, shutil, pathlib, os
        from pathlib import Path

        env_map = os.environ.copy()

        # --- Force the interpreter vLLM will use (its CMake expects VLLM_PYTHON_EXECUTABLE) ---
        sp_py       = spec["python"].command.path
        sp_py_bind  = str(spec["python"].prefix.bin)
        #env_map["PATH"]   = sp_py_bind + os.pathsep + env_map.get("PATH", "")
        #env_map["PYTHON"] = sp_py  # some helpers look at $PYTHON

        ## --- Build PYTHONPATH so CMake generators can import 'jinja2' (and friends) ---
        #def first_site_packages(dep_name: str):
        #    """Return first site-packages under the dependency prefix."""
        #    if dep_name not in spec:
        #        return None
        #    root = Path(spec[dep_name].prefix)
        #    for libdir in ("lib", "lib64"):
        #        for p in (root / libdir).rglob("site-packages"):
        #            if p.is_dir():
        #                return str(p)
        #    return None

        #py_paths = []
        #for dep in ("py-jinja2", "py-packaging", "py-regex", "py-torch"):
        #    sp = first_site_packages(dep)
        #    if sp:
        #        py_paths.append(sp)

        ## Keep any PYTHONPATH Spack already provided (e.g., for other deps)
        #if env_map.get("PYTHONPATH"):
        #    py_paths.append(env_map["PYTHONPATH"])

        #if py_paths:
        #    env_map["PYTHONPATH"] = os.pathsep.join(py_paths)
        #    # vLLM uses this for the Machete generator; harmless elsewhere
        #    env_map["VLLM_PYTHON_PATH"] = env_map["PYTHONPATH"]

        pybind = self.pkg.spec["py-pybind11"].prefix
        pybind_inc = os.path.join(str(pybind), "include")
        pybind_cmake = os.path.join(str(pybind), "share", "cmake", "pybind11")
        # help FlashMLA / subprojects find pybind11
        env_map["CMAKE_PREFIX_PATH"] = (
            (env_map.get("CMAKE_PREFIX_PATH", "") + (":" if env_map.get("CMAKE_PREFIX_PATH") else ""))
            + str(pybind)
        )
        env_map["CMAKE_INCLUDE_PATH"] = (
            (env_map.get("CMAKE_INCLUDE_PATH", "") + (":" if env_map.get("CMAKE_INCLUDE_PATH") else ""))
            + pybind_inc
        )
        env_map["CPLUS_INCLUDE_PATH"] = (
            (env_map.get("CPLUS_INCLUDE_PATH", "") + (":" if env_map.get("CPLUS_INCLUDE_PATH") else ""))
            + pybind_inc
        )
        # If any CMakeLists uses pybind11’s config:
        env_map["pybind11_DIR"] = pybind_cmake

        # Optional: some projects honor this env var too
        env_map["PYBIND11_SYSPATH"] = str(pybind)

        # --- CUDA/CUTLASS and parallelism hints ---
        cuda = spec["cuda"].prefix
        env_map["CUDA_HOME"] = str(cuda)
        env_map["MAX_JOBS"] = str(make_jobs)
        if "cutlass" in spec:
            env_map["VLLM_CUTLASS_SRC_DIR"] = str(spec["cutlass"].prefix)
            env_map['VLLM_CUTLASS_PREFIX'] = str(spec["cutlass"].prefix)

        # --- Compose CMAKE_ARGS that setup.py will forward to 'cmake' ---
        cmake_args = [
            f"-DVLLM_PYTHON_EXECUTABLE={sp_py}",     # vLLM expects this one
            "-DCMAKE_VERBOSE_MAKEFILE=ON",
            f"-DCUDAToolkit_ROOT={cuda}",
            f"-DCMAKE_CUDA_COMPILER={cuda}/bin/nvcc",
        ]
        extra = " ".join(cmake_args)
        env_map["CMAKE_ARGS"] = (extra if "CMAKE_ARGS" not in env_map
                                 else env_map["CMAKE_ARGS"] + " " + extra)

        # --- Run helper with Spack’s Python so Torch discovery happens in same env ---
        with working_dir(pkg.stage.source_path):
            spec["python"].command("use_existing_torch.py")

        ## --- Nuke stale CMake cache under setuptools' build temp (prevents sticky config) ---
        #try:
        #    plat = sysconfig.get_platform().replace("-", "_")
        #    btemp = pathlib.Path("build") / f"temp.{plat}"
        #    if btemp.exists():
        #        shutil.rmtree(btemp)
        #except Exception:
        #    pass  # best-effort cleanup

        # --- Standard pip install (no isolation), but with our env_map applied ---
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
