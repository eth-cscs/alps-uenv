# Copyright Spack Project Developers. See COPYRIGHT file for details.
#
# SPDX-License-Identifier: (Apache-2.0 OR MIT)


from spack_repo.builtin.build_systems.cuda import CudaPackage
from spack_repo.builtin.build_systems.python import PythonPackage

from spack.package import *


class PyTorchNvidiaApex(PythonPackage, CudaPackage):
    """A PyTorch Extension: Tools for easy mixed precision and
    distributed training in Pytorch"""

    homepage = "https://github.com/nvidia/apex/"
    git = "https://github.com/nvidia/apex/"
    url = "https://github.com/NVIDIA/apex/archive/refs/tags/24.04.01.tar.gz"

    license("BSD-3-Clause")

    version("master", branch="master")
    version("25.09", tag="25.09")
    #version("24.04.01", sha256="065bc5c0146ee579d5db2b38ca3949da4dc799b871961a2c9eb19e18892166ce")
    #version("23.08", tag="23.08")
    #version("23.07", tag="23.07")
    #version("23.06", tag="23.06")
    #version("23.05", tag="23.05")
    #version("22.03", tag="22.03")

    variant("cuda", default=True, description="Build with CUDA")

    # Based on the table of the readme on github
    #variant(
    #    "permutation_search_cuda", default=False, description="Build permutation search module"
    #)
    #variant("bnp", default=False, description="Build batch norm module")
    #variant("xentropy", default=False, description="Build cross entropy module")
    #variant("focal_loss_cuda", default=False, description="Build focal loss module")
    #variant("fused_index_mul_2d", default=False, description="Build fused_index_mul_2d module")
    #variant("fast_layer_norm", default=False, description="Build fast layer norm module")
    #variant("fmhalib", default=False, description="Build fmha module")
    #variant(
    #    "fast_multihead_attn", default=False, description="Build fast multihead attention module"
    #)
    #variant("transducer", default=False, description="Build transducer module")
    #variant("cudnn_gbn_lib", default=False, description="Build cudnn gbn module")
    #variant("peer_memory_cuda", default=False, description="Build peer memory module")
    #variant("nccl_p2p_cuda", default=False, description="Build with nccl p2p")
    #variant("fast_bottleneck", default=False, description="Build fast_bottleneck module")
    #variant("fused_conv_bias_relu", default=False, description="Build fused_conv_bias_relu moduel")

    #requires(
    #    "+peer_memory_cuda+nccl_p2p_cuda",
    #    when="+fast_bottleneck",
    #    msg="+fast_bottleneck requires both +peer_memory_cuda and +nccl_p2p_cuda to be enabled.",
    #)
    #requires("^cudnn@8.5:", when="+cudnn_gbn_lib")
    #requires("^cudnn@8.4:", when="+fused_conv_bias_relu")
    #requires("^nccl@2.10:", when="+nccl_p2p_cuda")

    depends_on("c", type="build")
    depends_on("cxx", type="build")

    with default_args(type=("build")):
        depends_on("ninja@1.11.1:")
        depends_on("py-setuptools")
        depends_on("py-packaging")
        depends_on("py-pip")
    with default_args(type=("build", "link", "run")):
        depends_on("python@3:")
        depends_on("py-torch@0.4:")
        for _arch in CudaPackage.cuda_arch_values:
            depends_on(f"py-torch+cuda cuda_arch={_arch}", when=f"+cuda cuda_arch={_arch}")
        depends_on("cudnn@8.5:", when="+cuda")
        depends_on("nccl@2.10:", when="+cuda")

    depends_on("py-pybind11", type=("build", "link", "run"))
    depends_on("cuda@9:", when="+cuda")

    ## https://github.com/NVIDIA/apex/issues/1498
    ## https://github.com/NVIDIA/apex/pull/1499
    #patch("1499.patch", when="@2020-10-19")
    #patch(
    #    "https://github.com/NVIDIA/apex/pull/1879.patch?full_index=1",
    #    sha256="8e2e21aa883d93e6c0ea0fecb812c8de906b2e77bcffeeb716adabd1dd76650e",
    #    when="@23.05:2019",
    #)

    #patch(
    #    "https://github.com/NVIDIA/apex/commit/e552ad997605dd883825106776eba230a6820345.patch?full_index=1",
    #    sha256="cd024471dce5cb7cb84607595055375d97f84f81c76f1f469cf4c9eb11a9063e",
    #    when="@:24.10",
    #)

    conflicts(
        "cuda_arch=none",
        when="+cuda",
        msg="Must specify CUDA compute capabilities of your GPU, see "
        "https://developer.nvidia.com/cuda-gpus",
    )

    #def torch_cuda_arch_list(self, env):
    #    if self.spec.satisfies("+cuda"):
    #        torch_cuda_arch = ";".join(
    #            "{0:.1f}".format(float(i) / 10.0) for i in self.spec.variants["cuda_arch"].value
    #        )
    #        env.set("TORCH_CUDA_ARCH_LIST", torch_cuda_arch)
    def torch_cuda_arch_list(self, env):
        """Set TORCH_CUDA_ARCH_LIST based on Spack's cuda_arch variant.
        Examples:
          80   -> 8.0
          86   -> 8.6
          90   -> 9.0
          90a  -> 9.0a
        """
        if not self.spec.satisfies("+cuda"):
            return

        arches = self.spec.variants["cuda_arch"].value
        # arches can be a single value or an iterable; normalize to list of strings
        if isinstance(arches, (str, int)):
            arches = [arches]
        arches = [str(a) for a in arches]

        def _fmt(a: str) -> str:
            # Handle the 'a' suffix (e.g., "90a" -> "9.0a")
            if a.endswith("a"):
                base = a[:-1]
                if not base.isdigit():
                    raise ValueError(f"Unrecognized cuda_arch value: {a}")
                num = int(base)
                return f"{num // 10}.{num % 10}a"
            # Pure numeric (e.g., "80" -> "8.0")
            if a.isdigit():
                num = int(a)
                return f"{num // 10}.{num % 10}"
            raise ValueError(f"Unrecognized cuda_arch value: {a}")

        torch_cuda_arch = ";".join(_fmt(a) for a in arches)
        env.set("TORCH_CUDA_ARCH_LIST", torch_cuda_arch)

    def setup_build_environment(self, env: EnvironmentModifications) -> None:
        env.set("APEX_CPP_EXT", "1")
        env.set("APEX_PARALLEL_BUILD", f"{make_jobs}")
        if self.spec.satisfies("+cuda"):
            env.set("CUDA_HOME", self.spec["cuda"].prefix)
            self.torch_cuda_arch_list(env)
            env.set("APEX_CUDA_EXT", "1")
            env.set("APEX_ALL_CONTRIB_EXT", "1")
            env.set("NVCC_APPEND_FLAGS", f"--threads {make_jobs}")
        else:
            env.unset("CUDA_HOME")

        #APEX_CPP_EXT=1 APEX_CUDA_EXT=1 APEX_ALL_CONTRIB_EXT=1
        #NVCC_APPEND_FLAGS="--threads 4" APEX_PARALLEL_BUILD=8
        #APEX_CPP_EXT=1 APEX_CUDA_EXT=1 APEX_FAST_MULTIHEAD_ATTN=1 APEX_FUSED_CONV_BIAS_RELU=1

        #APEX_PERMUTATION_SEARCH=1
        #APEX_BNP=1
        #APEX_XENTROPY=1
        #APEX_FOCAL_LOSS=1
        #APEX_INDEX_MUL_2D=1
        #APEX_FAST_LAYER_NORM=1
        #APEX_FMHA=1
        #APEX_FAST_MULTIHEAD_ATTN=1
        #APEX_TRANSDUCER=1
        #APEX_CUDNN_GBN=1

        #apex_C 	APEX_CPP_EXT=1
        #amp_C 	APEX_CUDA_EXT=1
        #syncbn 	APEX_CUDA_EXT=1
        #fused_layer_norm_cuda 	APEX_CUDA_EXT=1
        #mlp_cuda 	APEX_CUDA_EXT=1
        #scaled_upper_triang_masked_softmax_cuda 	APEX_CUDA_EXT=1
        #generic_scaled_masked_softmax_cuda 	APEX_CUDA_EXT=1
        #scaled_masked_softmax_cuda 	APEX_CUDA_EXT=1
        #fused_weight_gradient_mlp_cuda 	APEX_CUDA_EXT=1
        #permutation_search_cuda 	APEX_PERMUTATION_SEARCH=1
        #bnp 	APEX_BNP=1
        #xentropy 	APEX_XENTROPY=1
        #focal_loss_cuda 	APEX_FOCAL_LOSS=1
        #fused_index_mul_2d 	APEX_INDEX_MUL_2D=1
        #fast_layer_norm 	APEX_FAST_LAYER_NORM=1
        #fmhalib 	APEX_FMHA=1
        #fast_multihead_attn 	APEX_FAST_MULTIHEAD_ATTN=1
        #transducer_joint_cuda 	APEX_TRANSDUCER=1
        #transducer_loss_cuda 	APEX_TRANSDUCER=1
        #cudnn_gbn_lib 	APEX_CUDNN_GBN=1
        #peer_memory_cuda 	APEX_PEER_MEMORY=1
        #nccl_p2p_cuda 	APEX_NCCL_P2P=1
        #fast_bottleneck 	APEX_FAST_BOTTLENECK=1
        #fused_conv_bias_relu 	APEX_FUSED_CONV_BIAS_RELU=1
        #distributed_adam_cuda 	APEX_DISTRIBUTED_ADAM=1
        #distributed_lamb_cuda 	APEX_DISTRIBUTED_LAMB=1
        #_apex_nccl_allocator 	APEX_NCCL_ALLOCATOR=1
        #_apex_gpu_direct_storage 	APEX_GPU_DIRECT_STORAGE=1

    def setup_run_environment(self, env: EnvironmentModifications) -> None:
        self.torch_cuda_arch_list(env)

    #@when("^py-pip@:23.0")
    #def global_options(self, spec, prefix):
    #    args = []
    #    if spec.satisfies("^py-torch@1.0:"):
    #        args.append("--cpp_ext")
    #        if spec.satisfies("+cuda"):
    #            args.append("--cuda_ext")

    #    if spec.satisfies("+permutation_search_cuda"):
    #        args.append("--permutation_search")
    #    if spec.satisfies("+bnp"):
    #        args.append("--bnp")
    #    if spec.satisfies("+xentropy"):
    #        args.append("--xentropy")
    #    if spec.satisfies("+focal_loss_cuda"):
    #        args.append("--focal_loss")
    #    if spec.satisfies("+fused_index_mul_2d"):
    #        args.append("--index_mul_2d")
    #    if spec.satisfies("+fast_layer_norm"):
    #        args.append("--fast_layer_norm")
    #    if spec.satisfies("+fmhalib"):
    #        args.append("--fmha")
    #    if spec.satisfies("+fast_multihead_attn"):
    #        args.append("--fast_multihead_attn")
    #    if spec.satisfies("+transducer"):
    #        args.append("--transducer")
    #    if spec.satisfies("+cudnn_gbn_lib"):
    #        args.append("--cudnn_gbn")
    #    if spec.satisfies("+peer_memory_cuda"):
    #        args.append("--peer_memory")
    #    if spec.satisfies("+nccl_p2p_cuda"):
    #        args.append("--nccl_p2p")
    #    if spec.satisfies("+fast_bottleneck"):
    #        args.append("--fast_bottleneck")
    #    if spec.satisfies("+fused_conv_bias_relu"):
    #        args.append("--fused_conv_bias_relu")

    #    return args

    #@when("^py-pip@23.1:")
    #def config_settings(self, spec, prefix):
    #    global_options = ""
    #    if spec.satisfies("^py-torch@1.0:"):
    #        global_options += "--cpp_ext"
    #        if spec.satisfies("+cuda"):
    #            global_options += " --cuda_ext"

    #    if spec.satisfies("+permutation_search_cuda"):
    #        global_options += " --permutation_search"
    #    if spec.satisfies("+bnp"):
    #        global_options += " --bnp"
    #    if spec.satisfies("+xentropy"):
    #        global_options += " --xentropy"
    #    if spec.satisfies("+focal_loss_cuda"):
    #        global_options += " --focal_loss"
    #    if spec.satisfies("+fused_index_mul_2d"):
    #        global_options += " --index_mul_2d"
    #    if spec.satisfies("+fast_layer_norm"):
    #        global_options += " --fast_layer_norm"
    #    if spec.satisfies("+fmhalib"):
    #        global_options += " --fmha"
    #    if spec.satisfies("+fast_multihead_attn"):
    #        global_options += " --fast_multihead_attn"
    #    if spec.satisfies("+transducer"):
    #        global_options += " --transducer"
    #    if spec.satisfies("+cudnn_gbn_lib"):
    #        global_options += " --cudnn_gbn"
    #    if spec.satisfies("+peer_memory_cuda"):
    #        global_options += " --peer_memory"
    #    if spec.satisfies("+nccl_p2p_cuda"):
    #        global_options += " --nccl_p2p"
    #    if spec.satisfies("+fast_bottleneck"):
    #        global_options += " --fast_bottleneck"
    #    if spec.satisfies("+fused_conv_bias_relu"):
    #        global_options += " --fused_conv_bias_relu"

    #    return {
    #        "builddir": "build",
    #        "compile-args": f"-j{make_jobs}",
    #        "--global-option": global_options,
    #    }
