# PyTorch 2.8



## Full Diff w.r.t. https://github.com/spack/spack-packages.git@012d4b2c63b801a5287d994b29d5caf0096a68f8

    diff --git c/repos/spack_repo/builtin/packages/aws_ofi_nccl/package.py i/repos/spack_repo/builtin/packages/aws_ofi_nccl/package.py
    index ef81712934..3f9a6901fa 100644
    --- c/repos/spack_repo/builtin/packages/aws_ofi_nccl/package.py
    +++ i/repos/spack_repo/builtin/packages/aws_ofi_nccl/package.py
    @@ -68,6 +68,10 @@ class AwsOfiNccl(AutotoolsPackage):
         # To enable this plug-in to work with NCCL add it to the LD_LIBRARY_PATH
         def setup_run_environment(self, env: EnvironmentModifications) -> None:
             env.append_path("LD_LIBRARY_PATH", self.prefix.lib)
    +        env.set("NCCL_NET", "AWS Libfabric")
    +        env.set("NCCL_NET_GDR_LEVEL", "PHB")
    +        env.set("FI_CXI_DISABLE_HOST_REGISTER", "1")
    +        env.set("FI_MR_CACHE_MONITOR","userfaultfd")
     
         # To enable this plug-in to work with NCCL add it to the LD_LIBRARY_PATH
         def setup_dependent_run_environment(
    diff --git c/repos/spack_repo/builtin/packages/gloo/package.py i/repos/spack_repo/builtin/packages/gloo/package.py
    index 1ed88defa3..0369dc574a 100644
    --- c/repos/spack_repo/builtin/packages/gloo/package.py
    +++ i/repos/spack_repo/builtin/packages/gloo/package.py
    @@ -60,6 +60,16 @@ class Gloo(CMakePackage, CudaPackage):
         depends_on("cmake@2.8.12:", type="build")
         depends_on("libuv", when="platform=windows")
     
    +
    +    def patch(self):
    +        if self.compiler.name == "gcc" and self.compiler.version >= Version("14.0.0"):
    +            filter_file(
    +                'gloo_list_append_if_unique\(GLOO_NVCC_FLAGS "-std=c\+\+11"\)',
    +                'gloo_list_append_if_unique(GLOO_NVCC_FLAGS "-std=c++14")',
    +                "cmake/Cuda.cmake",
    +            )
    +
    +
         def cmake_args(self):
             return [
                 self.define_from_variant("USE_CUDA", "cuda"),
    diff --git c/repos/spack_repo/builtin/packages/nvshmem/package.py i/repos/spack_repo/builtin/packages/nvshmem/package.py
    index b730bea3f4..c7aface5af 100644
    --- c/repos/spack_repo/builtin/packages/nvshmem/package.py
    +++ i/repos/spack_repo/builtin/packages/nvshmem/package.py
    @@ -24,6 +24,7 @@ class Nvshmem(MakefilePackage, CMakePackage, CudaPackage):
     
         license("BSD-3-Clause-Open-MPI")
     
    +    version("3.4.5", sha256="40c1d4c255dd7395e04df41b181c4afdf2e0724c06b6fabde58bf2f8f532b0e5")
         version("3.3.9", sha256="ba41e9ad6650cf99c1a60a3e47c19d1d97d814add7d35ea72337520ae13eeb59")
         version("3.2.5-1", sha256="eb2c8fb3b7084c2db86bd9fd905387909f1dfd483e7b45f7b3c3d5fcf5374b5a")
         version("2.7.0-6", sha256="23ed9b0187104dc87d5d2bc1394b6f5ff29e8c19138dc019d940b109ede699df")
    @@ -91,6 +92,11 @@ class Nvshmem(MakefilePackage, CMakePackage, CudaPackage):
         depends_on("libfabric", when="+libfabric")
         depends_on("libfabric@1.15:", when="@3: +libfabric")
     
    +    def setup_run_environment(self, env: EnvironmentModifications) -> None:
    +        env.set("NVSHMEM_REMOTE_TRANSPORT", "libfabric")
    +        env.set("NVSHMEM_LIBFABRIC_PROVIDER", "cxi")
    +        env.set("NVSHMEM_DISABLE_CUDA_VMM", "1")
    +
     
     class CMakeBuilder(cmake.CMakeBuilder):
         def cmake_args(self):
    @@ -128,6 +134,30 @@ class CMakeBuilder(cmake.CMakeBuilder):
             if "+shmem" in self.spec:
                 config.append(self.define("SHMEM_HOME", self.spec["shmem"].prefix))
     
    +        config.append(self.define("NVSHMEM_DEFAULT_PMI2", "1"))
    +        config.append(self.define("NVSHMEM_DEFAULT_PMIX", "0"))
    +        config.append(self.define("NVSHMEM_PMI2_SUPPORT", "1"))
    +        config.append(self.define("NVSHMEM_PMIX_SUPPORT", "0"))
    +
    +        config.append(self.define("NVSHMEM_DISABLE_COLL_POLL", "1"))
    +        config.append(self.define("NVSHMEM_ENABLE_ALL_DEVICE_INLINING", "0"))
    +        config.append(self.define("NVSHMEM_GPU_COLL_USE_LDST", "0"))
    +        config.append(self.define("NVSHMEM_MPI_IS_OMPI", "0"))
    +        config.append(self.define("NVSHMEM_NVTX", "1"))
    +
    +        config.append(self.define("NVSHMEM_TEST_STATIC_LIB", "0"))
    +        config.append(self.define("NVSHMEM_TIMEOUT_DEVICE_POLLING", "0"))
    +        config.append(self.define("NVSHMEM_TRACE", "0"))
    +        config.append(self.define("NVSHMEM_USE_DLMALLOC", "0"))
    +
    +        config.append(self.define("NVSHMEM_VERBOSE", "0"))
    +        config.append(self.define("NVSHMEM_DEFAULT_UCX", "0"))
    +
    +        config.append(self.define("NVSHMEM_IBGDA_SUPPORT", "0"))
    +        config.append(self.define("NVSHMEM_IBGDA_SUPPORT_GPUMEM_ONLY", "0"))
    +        config.append(self.define("NVSHMEM_IBDEVX_SUPPORT", "0"))
    +        config.append(self.define("NVSHMEM_IBRC_SUPPORT", "0"))
    +
             return config
     
     
    diff --git c/repos/spack_repo/builtin/packages/py_torch/gcc-14.2-aarch64-2.8.patch i/repos/spack_repo/builtin/packages/py_torch/gcc-14.2-aarch64-2.8.patch
    new file mode 100644
    index 0000000000..5225e68623
    --- /dev/null
    +++ i/repos/spack_repo/builtin/packages/py_torch/gcc-14.2-aarch64-2.8.patch
    @@ -0,0 +1,49 @@
    +diff --git i/aten/src/ATen/cpu/vec/sve/vec_bfloat16.h w/aten/src/ATen/cpu/vec/sve/vec_bfloat16.h
    +index 7f05c2a..1632b59 100644
    +--- i/aten/src/ATen/cpu/vec/sve/vec_bfloat16.h
    ++++ w/aten/src/ATen/cpu/vec/sve/vec_bfloat16.h
    +@@ -220,8 +220,12 @@ class Vectorized<BFloat16> {
    +   Vectorized<BFloat16> le(const Vectorized<BFloat16>& other) const;
    + };
    + 
    +-inline std::tuple<Vectorized<float>, Vectorized<float>> convert_bfloat16_float(
    +-    const Vectorized<c10::BFloat16>& a) {
    ++#if defined(__GNUC__) && __GNUC__ == 14
    ++// Workaround for gcc-14.2.0 ICE during RTL pass: vregs when compiling for SVE
    ++__attribute__((optimize("no-tree-vectorize")))
    ++#endif
    ++inline std::tuple<Vectorized<float>, Vectorized<float>>
    ++convert_bfloat16_float(const Vectorized<c10::BFloat16>& a) {
    +   static_assert(
    +       Vectorized<c10::BFloat16>::size() == 2 * Vectorized<float>::size());
    +   auto zero = svreinterpret_bf16_f32(svdup_n_f32(0.0f));
    +diff --git i/aten/src/ATen/native/cpu/Activation.cpp w/aten/src/ATen/native/cpu/Activation.cpp
    +index 52d5383..00c9f4e 100644
    +--- i/aten/src/ATen/native/cpu/Activation.cpp
    ++++ w/aten/src/ATen/native/cpu/Activation.cpp
    +@@ -26,6 +26,10 @@ namespace at::native {
    + 
    + namespace {
    + 
    ++#if defined(__GNUC__) && __GNUC__ == 14 && defined(__aarch64__) && !defined(__ARM_FEATURE_SVE)
    ++// Workaround for gcc-14.2.0 ICE during RTL pass: expand when compiling for NEON
    ++__attribute__((optimize("no-tree-vectorize")))
    ++#endif
    + static void log_sigmoid_cpu_kernel(TensorBase &output, TensorBase &buffer, const TensorBase &input) {
    +   if (at::isReducedFloatingType(input.scalar_type())) {
    +     AT_DISPATCH_REDUCED_FLOATING_TYPES(input.scalar_type(), "log_sigmoid_cpu", [&]() {
    +diff --git i/aten/src/ATen/native/cpu/Unfold2d.cpp w/aten/src/ATen/native/cpu/Unfold2d.cpp
    +index 8ef0741..d8d9c26 100644
    +--- i/aten/src/ATen/native/cpu/Unfold2d.cpp
    ++++ w/aten/src/ATen/native/cpu/Unfold2d.cpp
    +@@ -169,6 +169,10 @@ static void unfolded2d_acc_channels_last(
    + 
    + /* note: due to write issues, this one cannot be parallelized as well as
    +  * unfolded2d_copy */
    ++// if defined(__GNUC__) && __GNUC__ == 14 && defined(__ARM_FEATURE_SVE) && !defined(__ARM_FEATURE_BF16)
    ++// Workaround for gcc-14.2.0 ICE during RTL pass: vregs when compiling for SVE without BF16
    ++__attribute__((optimize("no-tree-vectorize")))
    ++// endif
    + void unfolded2d_acc_kernel(
    +     ScalarType dtype,
    +     void *finput_data,
    diff --git c/repos/spack_repo/builtin/packages/py_torch/package.py i/repos/spack_repo/builtin/packages/py_torch/package.py
    index 59bb0b3678..205afe9748 100644
    --- c/repos/spack_repo/builtin/packages/py_torch/package.py
    +++ i/repos/spack_repo/builtin/packages/py_torch/package.py
    @@ -332,6 +332,9 @@ class PyTorch(PythonPackage, CudaPackage, ROCmPackage):
     
         conflicts("%gcc@:9.3", when="@2.2:", msg="C++17 support required")
     
    +    # https://github.com/pytorch/pytorch/pull/157867
    +    patch("gcc-14.2-aarch64-2.8.patch", when="@2.8 %gcc@14.2:")
    +
         # https://github.com/pytorch/pytorch/issues/160092
         patch(
             "https://github.com/pytorch/pytorch/commit/231c72240d80091f099c95e326d3600cba866eee.patch?full_index=1",
    @@ -785,6 +788,11 @@ class PyTorch(PythonPackage, CudaPackage, ROCmPackage):
             else:
                 env.set("BUILD_CUSTOM_PROTOBUF", "OFF")
     
    +        if self.spec.satisfies("%gcc@14:"):
    +            env.set("CMAKE_C_FLAGS", "-Wno-incompatible-pointer-types")
    +
    +        env.set("USE_PRIORITIZED_TEXT_FOR_LD", "1")
    +
         def setup_run_environment(self, env: EnvironmentModifications) -> None:
             self.torch_cuda_arch_list(env)
