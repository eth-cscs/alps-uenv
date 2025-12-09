from spack.package import *
import os
import re


class NvidiaMathdx(Package):
    """NVIDIA MathDX: device-side math libraries (cuBLASDx, cuFFTDx, cuRANDDx,
    cuSolverDx, nvCOMPDx). Installs headers, fatbins, and CMake package files
    for `find_package(mathdx)`. By default uses Spack's CUTLASS instead of the
    vendored one under external/."""

    homepage = "https://developer.nvidia.com/"
    maintainers = ["your-github-handle"]

    version(
        "25.06.1-cuda13",
        sha256="81646046e7ae57169fcea79fb59df526eaef65e740b66e291a69182c612b8304",
        url="https://developer.nvidia.com/downloads/compute/cuFFTDx/redist/cuFFTDx/cuda13/nvidia-mathdx-25.06.1-cuda13.tar.gz",
        expand=True,
    )
    version(
        "25.06.1-cuda12",
        sha256="d4952f6e1a7864d29d9ec4e01c21628d84086e941cf4a3da2df1e11ba5f13f84",
        url="https://developer.nvidia.com/downloads/compute/cuFFTDx/redist/cuFFTDx/cuda12/nvidia-mathdx-25.06.1-cuda12.tar.gz",
        expand=True,
    )

    depends_on("cuda@13:", when="@25.06.1-cuda13:")
    depends_on("cuda@12:", when="@25.06.1-cuda12:")

    conflicts("^cuda@12", when="@25.06.1-cuda13:")
    conflicts("^cuda@13:", when="@25.06.1-cuda12:")

    variant("external-cutlass", default=False,
            description="Install vendored external/cutlass")
    depends_on("cutlass@3.9.0:", when="~external-cutlass")

    phases = ["install"]

    # --- Helpers -------------------------------------------------------------

    def _find_mathdx_root(self):
        # Find the dir that contains both 'include' and 'lib'
        src = self.stage.source_path
        for root, dirs, _ in os.walk(src):
            if "include" in dirs and "lib" in dirs:
                return root
        raise InstallError("Could not locate MathDX root (dir with both 'include' and 'lib').")

    def _patch_mathdx_config(self, prefix):
        cfg = os.path.join(prefix, "lib", "cmake", "mathdx", "mathdx-config.cmake")
        if not os.path.isfile(cfg):
            tty.warn("mathdx-config.cmake not found to patch; CMake consumers might fail to find CUTLASS.")
            return

        with open(cfg, "r", encoding="utf-8") as f:
            text = f.read()

        pattern = r"(?s)# CUTLASS.*?# commondx"
        replacement = r"""# CUTLASS (patched by Spack: prefer system CUTLASS, no vendored fallback)
    set(mathdx_DEPENDENCY_CUTLASS_RESOLVED FALSE)
    set(mathdx_CUTLASS_MIN_VERSION 3.9.0)

    find_package(NvidiaCutlass QUIET)
    if(${NvidiaCutlass_FOUND})
        if(${NvidiaCutlass_VERSION} VERSION_LESS ${mathdx_CUTLASS_MIN_VERSION})
            message(FATAL_ERROR "Found CUTLASS version is ${NvidiaCutlass_VERSION}, minimal required version is ${mathdx_CUTLASS_MIN_VERSION}")
        endif()
        get_property(mathdx_NvidiaCutlass_include_dir TARGET nvidia::cutlass::cutlass PROPERTY INTERFACE_INCLUDE_DIRECTORIES)
        set_and_check(mathdx_cutlass_INCLUDE_DIR "${mathdx_NvidiaCutlass_include_dir}")
        if(NOT ${CMAKE_FIND_PACKAGE_NAME}_FIND_QUIETLY)
            message(STATUS "mathdx: Using CUTLASS from NvidiaCutlass package: ${mathdx_NvidiaCutlass_include_dir}")
        endif()
        set(mathdx_DEPENDENCY_CUTLASS_RESOLVED TRUE)
    elseif(DEFINED mathdx_CUTLASS_ROOT)
        get_filename_component(mathdx_CUTLASS_ROOT_ABSOLUTE ${mathdx_CUTLASS_ROOT} ABSOLUTE)
        set_and_check(mathdx_cutlass_INCLUDE_DIR  "${mathdx_CUTLASS_ROOT_ABSOLUTE}/include")
        if(NOT ${CMAKE_FIND_PACKAGE_NAME}_FIND_QUIETLY)
            message(STATUS "mathdx: Using CUTLASS via mathdx_CUTLASS_ROOT: ${mathdx_CUTLASS_ROOT_ABSOLUTE}")
        endif()
        set(mathdx_DEPENDENCY_CUTLASS_RESOLVED TRUE)
    elseif(DEFINED ENV{mathdx_CUTLASS_ROOT})
        get_filename_component(mathdx_CUTLASS_ROOT_ABSOLUTE $ENV{mathdx_CUTLASS_ROOT} ABSOLUTE)
        set_and_check(mathdx_cutlass_INCLUDE_DIR "${mathdx_CUTLASS_ROOT_ABSOLUTE}/include")
        if(NOT ${CMAKE_FIND_PACKAGE_NAME}_FIND_QUIETLY)
            message(STATUS "mathdx: Using CUTLASS via ENV{mathdx_CUTLASS_ROOT}: ${mathdx_CUTLASS_ROOT_ABSOLUTE}")
        endif()
        set(mathdx_DEPENDENCY_CUTLASS_RESOLVED TRUE)
    endif()

    if(NOT ${mathdx_DEPENDENCY_CUTLASS_RESOLVED})
        set(${CMAKE_FIND_PACKAGE_NAME}_FOUND FALSE)
        if(${CMAKE_FIND_PACKAGE_NAME}_FIND_REQUIRED)
            message(FATAL_ERROR "${CMAKE_FIND_PACKAGE_NAME} package NOT FOUND - dependency missing:\n"
                                "  Missing CUTLASS dependency.\n"
                                "  Provide it via mathdx_CUTLASS_ROOT or NvidiaCutlass package (NvidiaCutlass_ROOT/NvidiaCutlass_DIR).\n")
        endif()
    endif()

    # commondx
"""
        new_text, nsubs = re.subn(pattern, replacement, text)
        if nsubs == 0:
            tty.warn("Spack patch: did not find CUTLASS section to replace in mathdx-config.cmake; leaving as-is.")
        else:
            with open(cfg, "w", encoding="utf-8") as f:
                f.write(new_text)
            tty.msg("Patched mathdx-config.cmake to use system CUTLASS (no vendored fallback).")

    def _prune_static_archives_if_needed(self, prefix, spec):
        """Remove *.a on non-x86 targets; keep them only on x86."""
        # Spack target families commonly: x86_64, aarch64, ppc64le, etc.
        fam = str(spec.target.family)
        is_x86 = fam in ("x86_64", "x86")
        if is_x86:
            tty.msg("Keeping static archives (*.a) for x86 target family: %s" % fam)
            return

        removed = 0
        for root, _dirs, files in os.walk(prefix.lib):
            for fname in files:
                if fname.endswith(".a"):
                    try:
                        os.remove(os.path.join(root, fname))
                        removed += 1
                    except OSError:
                        pass
        if removed:
            tty.msg("Pruned %d static archive(s) (*.a) on non-x86 target family: %s" % (removed, fam))

    # --- Install -------------------------------------------------------------

    def install(self, spec, prefix):
        root = self._find_mathdx_root()

        # Headers
        install_tree(os.path.join(root, "include"), prefix.include)

        # Libraries (lib/cmake/**, *.fatbin, and (temporarily) *.a)
        install_tree(os.path.join(root, "lib"), prefix.lib)

        # Optional top-level cmake (rare)
        top_cmake = os.path.join(root, "cmake")
        if os.path.isdir(top_cmake):
            install_tree(top_cmake, os.path.join(prefix, "cmake"))

        # Docs/examples -> share
        doc_src = os.path.join(root, "doc")
        ex_src = os.path.join(root, "example")
        if os.path.isdir(doc_src):
            install_tree(doc_src, os.path.join(prefix, "share", "nvidia-mathdx", "doc"))
        if os.path.isdir(ex_src):
            install_tree(ex_src, os.path.join(prefix, "share", "nvidia-mathdx", "example"))

        # CUTLASS handling
        if "+external-cutlass" in spec:
            ext_dir = os.path.join(root, "external")
            if os.path.isdir(ext_dir):
                install_tree(ext_dir, os.path.join(prefix, "external"))
        else:
            self._patch_mathdx_config(prefix)

        # Remove *.a archives when not on x86
        self._prune_static_archives_if_needed(prefix, spec)

    # --- Environments --------------------------------------------------------

    def setup_dependent_build_environment(self, env, dependent_spec):
        env.set("mathdx_ROOT", self.prefix)
        if "~external-cutlass" in self.spec:
            env.set("mathdx_CUTLASS_ROOT", self.spec["cutlass"].prefix)

    def setup_run_environment(self, env):
        env.set("mathdx_ROOT", self.prefix)

    @run_after("install")
    def sanity_check_install(self):
        if not os.path.isdir(self.prefix.include):
            raise InstallError("MathDX headers missing (prefix/include not found).")
        if not os.path.isdir(self.prefix.lib):
            raise InstallError("MathDX lib directory missing.")
        cmake_root = os.path.join(self.prefix.lib, "cmake")
        if not os.path.isdir(cmake_root):
            tty.warn("lib/cmake not found; check bundle layout.")
