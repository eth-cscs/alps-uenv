# Copyright Spack Project Developers. See COPYRIGHT file for details.
#
# SPDX-License-Identifier: (Apache-2.0 OR MIT)


from spack.package import *


class PyTorchNvidiaApex(PythonPackage, CudaPackage):
    """A PyTorch Extension: Tools for easy mixed precision and
    distributed training in Pytorch"""

    homepage = "https://github.com/nvidia/apex/"
    git = "https://github.com/nvidia/apex/"
    url = "https://github.com/NVIDIA/apex/archive/refs/tags/24.04.01.tar.gz"

    license("BSD-3-Clause")

    version("master", branch="master")
    version("25.02.14", commit="b216eeee7dd91478745496919e9c0167cc4c41e3")
    version(
        "24.04.01",
        sha256="065bc5c0146ee579d5db2b38ca3949da4dc799b871961a2c9eb19e18892166ce",
        preferred=True,
    )
    version("23.08", tag="23.08")
    version("23.07", tag="23.07")
    version("23.06", tag="23.06")
    version("23.05", tag="23.05")
    version("22.03", tag="22.03")
    version("2020-10-19", commit="8a1ed9e8d35dfad26fb973996319965e4224dcdd", deprecated=True)

    depends_on("c", type="build")
    depends_on("cxx", type="build")

    variant("cuda", default=True, description="Build with CUDA")

    # Based on the table of the readme on github
    variant(
        "permutation_search_cuda", default=True, description="Build permutation search module"
    )
    variant("bnp", default=True, description="Build batch norm module")
    variant("xentropy", default=True, description="Build cross entropy module")
    variant("focal_loss", default=True, description="Build focal loss module")
    variant("index_mul_2d", default=True, description="Build fused_index_mul_2d module")
    variant("fast_layer_norm", default=True, description="Build fast layer norm module")
    variant("fmha", default=True, description="Build fmha module")
    variant(
        "fast_multihead_attn", default=True, description="Build fast multihead attention module"
    )
    variant("transducer", default=True, description="Build transducer module")
    variant("cudnn_gbn", default=True, description="Build cudnn gbn module")
    variant("peer_memory", default=True, description="Build peer memory module")
    variant("nccl_p2p", default=True, description="Build with nccl p2p")
    variant("fast_bottleneck", default=True, description="Build fast_bottleneck module")
    variant("fused_conv_bias_relu", default=True, description="Build fused_conv_bias_relu moduel")
    variant("distributed_adam", when="+cuda", default=True, description="CUDA kernels for multi-tensor Adam optimizer")
    variant("distributed_lamb", when="+cuda", default=True, description="CUDA kernels for multi-tensor Lamb optimizer")
    variant("permutation_search", when="+cuda", default=True, description="CUDA kernels for permutation search")
    variant("focal_loss", when="+cuda", default=True, description="CUDA kernels for focal loss")
    variant("group_norm", when="+cuda", default=True, description="CUDA kernels for group normalization")
    variant("index_mul_2d", when="+cuda", default=True, description="CUDA kernels for index mul calculations")
    variant("deprecated_fused_adam", when="+cuda", default=False, description="CUDA kernels for fused Adam optimizer")
    variant("deprecated_fused_lamb", when="+cuda", default=False, description="CUDA kernels for fused Lamb optimizer")
    variant("nccl_allocator", when="+cuda", default=True, description="NCCL allocator support")
    variant("gpu_direct_storage", when="+cuda", default=True, description="GPU direct storage support")

    requires(
        "+peer_memory+nccl_p2p",
        when="+fast_bottleneck",
        msg="+fast_bottleneck requires both +peer_memory and +nccl_p2p to be enabled.",
    )
    with default_args(type=("build")):
        depends_on("py-setuptools")
        depends_on("py-packaging")
        depends_on("py-pip")
        depends_on("ninja")
    with default_args(type=("build", "run")):
        depends_on("python@3:")
        depends_on("py-torch@0.4:")
        for _arch in CudaPackage.cuda_arch_values:
            depends_on(f"py-torch+cuda cuda_arch={_arch}", when=f"+cuda cuda_arch={_arch}")
    with default_args(type=("build", "link", "run")):
        depends_on("py-pybind11")
        depends_on("cudnn@8.5:", when="+cudnn_gbn")
        depends_on("cudnn@8.4:", when="+fast_bottleneck")
        depends_on("cudnn@8.4:", when="+fused_conv_bias_relu")
        depends_on("nccl@2.10.3:", when="+nccl_p2p")
        depends_on("nccl@2.19:", when="+nccl_allocator")

    depends_on("cuda@9:", when="+cuda")
    depends_on("cuda@11:", when="+fmha")

    # https://github.com/NVIDIA/apex/issues/1498
    # https://github.com/NVIDIA/apex/pull/1499
    patch("1499.patch", when="@2020-10-19")
    patch(
        "https://github.com/NVIDIA/apex/pull/1879.patch?full_index=1",
        sha256="8e2e21aa883d93e6c0ea0fecb812c8de906b2e77bcffeeb716adabd1dd76650e",
        when="@23.05:2019",
    )

    patch(
        "https://github.com/NVIDIA/apex/pull/1855.patch?full_index=1",
        sha256="8481b1234a9ce1e8bef4e57a259d8528107761e1843777489e815ec3727397fd",
        when="@:24.10",
    )

    conflicts(
        "cuda_arch=none",
        when="+cuda",
        msg="Must specify CUDA compute capabilities of your GPU, see "
        "https://developer.nvidia.com/cuda-gpus",
    )

    def torch_cuda_arch_list(self, env):
        if self.spec.satisfies("+cuda"):
            torch_cuda_arch = ";".join(
                "{0:.1f}".format(float(i) / 10.0) for i in self.spec.variants["cuda_arch"].value
            )
            env.set("TORCH_CUDA_ARCH_LIST", torch_cuda_arch)

    def setup_build_environment(self, env):
        if self.spec.satisfies("+cuda"):
            env.set("CUDA_HOME", self.spec["cuda"].prefix)
            self.torch_cuda_arch_list(env)
        else:
            env.unset("CUDA_HOME")

    def setup_run_environment(self, env):
        self.torch_cuda_arch_list(env)

    @when("^py-pip@:23.0")
    def global_options(self, spec, prefix):
        args = []
        variant_to_arg = lambda v: args.append(f"--{v}") if spec.satisfies(f"+{v}") else None
        if spec.satisfies("^py-torch@1.0:"):
            args.append("--cpp_ext")
            if spec.satisfies("+cuda"):
                args.append("--cuda_ext")
                variant_to_arg("distributed_adam")
                variant_to_arg("distributed_lamb")
                variant_to_arg("permutation_search")
                variant_to_arg("bnp")
                variant_to_arg("xentropy")
                variant_to_arg("focal_loss")
                variant_to_arg("group_norm")
                variant_to_arg("index_mul_2d")
                variant_to_arg("deprecated_fused_adam")
                variant_to_arg("deprecated_fused_lamb")
                variant_to_arg("fast_layer_norm")
                variant_to_arg("fmha")
                variant_to_arg("fast_multihead_attn")
                variant_to_arg("transducer")
                variant_to_arg("cudnn_gbn")
                variant_to_arg("peer_memory")
                variant_to_arg("nccl_p2p")
                variant_to_arg("fast_bottleneck")
                variant_to_arg("fused_conv_bias_relu")
                variant_to_arg("nccl_allocator")
                variant_to_arg("gpu_direct_storage")
        return args

    @when("^py-pip@23.1:")
    def config_settings(self, spec, prefix):
        args = ""
        
        def variant_to_arg(v):
            nonlocal args
            if spec.satisfies(f"+{v}"):
                args += f" --{v}"
        
        if spec.satisfies("^py-torch@1.0:"):
            args="--cpp_ext"
            if spec.satisfies("+cuda"):
                args += " --cuda_ext"
                variant_to_arg("distributed_adam")
                variant_to_arg("distributed_lamb")
                variant_to_arg("permutation_search")
                variant_to_arg("bnp")
                variant_to_arg("xentropy")
                variant_to_arg("focal_loss")
                variant_to_arg("group_norm")
                variant_to_arg("index_mul_2d")
                variant_to_arg("deprecated_fused_adam")
                variant_to_arg("deprecated_fused_lamb")
                variant_to_arg("fast_layer_norm")
                variant_to_arg("fmha")
                variant_to_arg("fast_multihead_attn")
                variant_to_arg("transducer")
                variant_to_arg("cudnn_gbn")
                variant_to_arg("peer_memory")
                variant_to_arg("nccl_p2p")
                variant_to_arg("fast_bottleneck")
                variant_to_arg("fused_conv_bias_relu")
                variant_to_arg("nccl_allocator")
                variant_to_arg("gpu_direct_storage")
        return {
            "builddir": "build",
            "compile-args": f"-j{make_jobs}",
            "--build-option": args,
        }
