# Copyright Spack Project Developers. See COPYRIGHT file for details.
#
# SPDX-License-Identifier: (Apache-2.0 OR MIT)

# pytorch uenv: custom py-triton, taken from the vllm uenv recipe
# (/users/bcumming/uenv/vllm/recipe, 3.7.1) and extended to 3.8.0 for torch 2.14:
# - 3.8 moved the llvm pin from cmake/llvm-hash.txt to cmake/llvm-info.json ("llvm_hash")
# - 3.8 builds the GSan device runtime (gsan.ll) with ${LLVM_SYSPATH}/bin/clang++, so the
#   pinned llvm must include clang (triton's scripts/build-llvm-project.sh uses
#   mlir;llvm;lld;clang)
#
# vllm uenv notes:
# - upstream spack-packages (releases/v2026.10) stops at 3.4.0; torch 2.13 needs 3.7.1
# - triton needs the exact llvm-project commit in cmake/llvm-hash.txt. Instead of
#   git-cloning llvm-project at build time (as the old alps pytorch recipe did), the
#   llvm source is a checksummed resource() and is built into <prefix>/triton-llvm.
# - the LLVM build is memory-hungry at link time: link jobs are capped
#   (LLVM_PARALLEL_LINK_JOBS), compile jobs follow spack's make_jobs.
# - triton's setup.py normally downloads ptxas/cuobjdump/nvdisasm/cuda headers; we build
#   offline and symlink the tools (backends/nvidia/bin) and CUDA/CUPTI headers
#   (backends/nvidia/include, needed by the runtime JIT) from the spack cuda into the
#   installed backend instead (views do not apply setup_run_environment, so env vars are
#   not enough).

import glob
import os

from spack_repo.builtin.build_systems.python import PythonPackage

from spack.package import *

# maximum number of concurrent LLVM link jobs: each lld/ld of an LLVM/MLIR tool can
# use several GB of memory.
LLVM_LINK_JOBS = 8


class PyTriton(PythonPackage):
    """A language and compiler for custom Deep Learning operations."""

    homepage = "https://github.com/triton-lang/triton"
    url = "https://github.com/triton-lang/triton/archive/refs/tags/v3.7.1.tar.gz"
    git = "https://github.com/triton-lang/triton.git"

    license("MIT")

    # 3.8.0 is the version pinned by py-torch@2.14 (.ci/docker/triton_version.txt)
    version("3.8.0", sha256="d50981f98bf61a5ce21d2a0c6ac067c20b7f741acf3bee4b8370edc3b63fd337")
    version("3.7.1", sha256="7d998625d1035ac496d06a81117727647169422ee67b8889609f06fd5367c491")

    # llvm-project commit from triton v3.8.0 cmake/llvm-info.json
    resource(
        name="llvm-project",
        url="https://github.com/llvm/llvm-project/archive/5f07f818b51b786b0a87b4e514882600ecba112f.tar.gz",
        sha256="c165c01a3e6c0e12f0794d387f2f3b0740e2b30ceeee10cc4d6e0adba5044ff3",
        destination=".",
        placement="llvm-project",
        when="@3.8.0",
    )

    # llvm-project commit from triton v3.7.1 cmake/llvm-hash.txt
    resource(
        name="llvm-project",
        url="https://github.com/llvm/llvm-project/archive/1f126a6dea50d185c0781743a667390037ae88bd.tar.gz",
        sha256="72d33c6192627cd2f7ba96bdeffc319c0d69a53dc026b75e9d086decb368947f",
        destination=".",
        placement="llvm-project",
        when="@3.7.1",
    )

    depends_on("c", type="build")
    depends_on("cxx", type="build")

    with default_args(type="build"):
        depends_on("cmake@3.20:3")
        depends_on("ninja@1.11.1:")
        depends_on("py-setuptools@40.8.0:")
        depends_on("py-wheel")
        depends_on("py-pybind11@2.13.1:")
        depends_on("py-lit")
        depends_on("nlohmann-json")

    depends_on("python@3.10:", type=("build", "run"))
    depends_on("zlib-api", type="link")
    conflicts("^openssl@3.3.0")
    depends_on("cuda", type=("build", "run"))

    def _cuda_tools(self):
        cuda = self.spec["cuda"].prefix
        return {
            "ptxas": cuda.bin.ptxas,
            "ptxas-blackwell": cuda.bin.ptxas,
            "cuobjdump": cuda.bin.cuobjdump,
            "nvdisasm": cuda.bin.nvdisasm,
        }

    def setup_build_environment(self, env: EnvironmentModifications) -> None:
        cuda = self.spec["cuda"].prefix
        env.set("TRITON_OFFLINE_BUILD", "1")
        env.set("MAX_JOBS", str(make_jobs))
        env.set("JSON_SYSPATH", self.spec["nlohmann-json"].prefix)
        env.set("PYBIND11_SYSPATH", self.spec["py-pybind11"].prefix)
        env.set("CUDA_HOME", cuda)
        env.set("TRITON_PTXAS_PATH", cuda.bin.ptxas)
        env.set("TRITON_PTXAS_BLACKWELL_PATH", cuda.bin.ptxas)
        env.set("TRITON_CUOBJDUMP_PATH", cuda.bin.cuobjdump)
        env.set("TRITON_NVDISASM_PATH", cuda.bin.nvdisasm)
        env.set("TRITON_CUDACRT_PATH", cuda.include)
        env.set("TRITON_CUDART_PATH", cuda.include)
        # proton expects cupti.h and cuda.h in the same directory: merged dir is made
        # in a run_before("install") step below
        env.set("TRITON_CUPTI_INCLUDE_PATH", join_path(self.stage.path, "cuda-include"))
        env.set("TRITON_CUPTI_LIB_PATH", join_path(cuda, "extras", "CUPTI", "lib64"))
        # 3.8 adds a separate (downloaded) Blackwell CUPTI; use the spack cuda's CUPTI
        env.set("TRITON_CUPTI_LIB_BLACKWELL_PATH", join_path(cuda, "extras", "CUPTI", "lib64"))
        # the llvm built by build_llvm()
        llvm = join_path(self.prefix, "triton-llvm")
        env.set("LLVM_SYSPATH", llvm)
        env.set("LLVM_INCLUDE_DIRS", join_path(llvm, "include"))
        env.set("LLVM_LIBRARY_DIR", join_path(llvm, "lib"))
        # force spack's compiler: LLVM's exported cmake config can override it
        env.set(
            "TRITON_APPEND_CMAKE_ARGS",
            " ".join(
                [
                    f"-DCMAKE_C_COMPILER={self.compiler.cc}",
                    f"-DCMAKE_CXX_COMPILER={self.compiler.cxx}",
                    "-DCMAKE_BUILD_WITH_INSTALL_RPATH=ON",
                    f"-DZLIB_ROOT={self.spec['zlib-api'].prefix}",
                ]
            ),
        )

    @run_before("install")
    def build_llvm(self):
        """Build the pinned llvm-project (mlir;llvm;lld) into <prefix>/triton-llvm."""
        src = join_path(self.stage.source_path, "llvm-project")
        build = join_path(self.stage.path, "llvm-build")
        install = join_path(self.prefix, "triton-llvm")
        mkdirp(build)
        cmake = which("cmake", required=True)
        ninja = which("ninja", required=True)
        cmake(
            "-G",
            "Ninja",
            "-DCMAKE_BUILD_TYPE=Release",
            f"-DCMAKE_C_COMPILER={self.compiler.cc}",
            f"-DCMAKE_CXX_COMPILER={self.compiler.cxx}",
            "-DLLVM_CCACHE_BUILD=OFF",
            "-DLLVM_ENABLE_ASSERTIONS=ON",
            "-DLLVM_BUILD_TOOLS=ON",
            "-DLLVM_INSTALL_TOOLS=ON",
            "-DLLVM_INSTALL_UTILS=ON",
            "-DLLVM_OPTIMIZED_TABLEGEN=ON",
            "-DLLVM_ENABLE_TERMINFO=OFF",
            "-DLLVM_ENABLE_ZSTD=OFF",
            "-DLLVM_INCLUDE_TESTS=OFF",
            "-DLLVM_INCLUDE_BENCHMARKS=OFF",
            "-DLLVM_INCLUDE_EXAMPLES=OFF",
            "-DMLIR_INCLUDE_TESTS=OFF",
            # same target/project set as triton's official llvm builds; 3.8 also needs
            # clang (third_party/nvidia/CMakeLists.txt builds gsan.ll with clang++)
            "-DLLVM_TARGETS_TO_BUILD=Native;NVPTX;AMDGPU",
            "-DLLVM_ENABLE_PROJECTS="
            + ("mlir;llvm;lld;clang" if self.spec.satisfies("@3.8:") else "mlir;llvm;lld"),
            f"-DLLVM_PARALLEL_LINK_JOBS={min(LLVM_LINK_JOBS, make_jobs)}",
            f"-DCMAKE_INSTALL_PREFIX={install}",
            "-B",
            build,
            join_path(src, "llvm"),
        )
        ninja("-C", build, f"-j{make_jobs}", "install")
        # the llvm build tree is large (tens of GB) and lives in the (RAM backed) stage
        remove_linked_tree(build)

    @run_before("install")
    def create_cuda_include_dir(self):
        """Merged include dir with CUDA and CUPTI headers (needed by proton)."""
        cuda = self.spec["cuda"].prefix
        merged = join_path(self.stage.path, "cuda-include")
        mkdirp(merged)
        for d in (cuda.include, join_path(cuda, "extras", "CUPTI", "include")):
            for entry in os.listdir(d):
                dst = join_path(merged, entry)
                if os.path.lexists(dst):
                    os.remove(dst)
                symlink(join_path(d, entry), dst)

    @run_after("install")
    def remove_llvm(self):
        """LLVM is linked statically into libtriton.so: drop the multi-GB install tree."""
        llvm = join_path(self.prefix, "triton-llvm")
        if os.path.isdir(llvm):
            remove_linked_tree(llvm)

    @run_after("install")
    def link_cuda_tools(self):
        """Point the installed nvidia backend at spack's CUDA tools and headers (idempotent).

        bin/: ptxas, cuobjdump, nvdisasm (official wheels ship them; the offline build does not).
        include/: the runtime JIT compiles backends/nvidia/driver.c (-> cuda_utils.so) with
        -I <backend>/include and needs cuda.h; official wheels ship CUDA + CUPTI headers there.
        Without it the first GPU use fails compiling cuda_utils.c.
        """
        cuda = self.spec["cuda"].prefix
        header_dirs = [cuda.include, join_path(cuda, "extras", "CUPTI", "include")]
        for backend in glob.glob(
            join_path(self.prefix, "lib", "python*", "site-packages", "triton", "backends", "nvidia")
        ):
            bindir = join_path(backend, "bin")
            mkdirp(bindir)
            for name, target in self._cuda_tools().items():
                dst = join_path(bindir, name)
                if os.path.lexists(dst):
                    os.remove(dst)
                symlink(target, dst)

            incdir = join_path(backend, "include")
            mkdirp(incdir)
            for d in header_dirs:
                for entry in os.listdir(d):
                    dst = join_path(incdir, entry)
                    if os.path.lexists(dst):
                        os.remove(dst)
                    symlink(join_path(d, entry), dst)

    def setup_run_environment(self, env: EnvironmentModifications) -> None:
        cuda = self.spec["cuda"].prefix
        env.set("TRITON_PTXAS_PATH", cuda.bin.ptxas)
        env.set("TRITON_CUOBJDUMP_PATH", cuda.bin.cuobjdump)
        env.set("TRITON_NVDISASM_PATH", cuda.bin.nvdisasm)

    @property
    def build_directory(self):
        return "."
