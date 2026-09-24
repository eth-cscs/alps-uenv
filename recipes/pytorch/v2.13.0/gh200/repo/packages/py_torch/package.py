# Copyright Spack Project Developers. See COPYRIGHT file for details.
#
# SPDX-License-Identifier: (Apache-2.0 OR MIT)

from spack_repo.builtin.packages.py_torch.package import PyTorch as BuiltinPyTorch


class PyTorch(BuiltinPyTorch):
    """Tensors and dynamic neural networks with GPU acceleration."""

    def setup_build_environment(self, env):
        super().setup_build_environment(env)
        if "+gloo" in self.spec:
            # The external Gloo build cannot enable c10 dtypes without creating
            # a dependency cycle, so it lacks the CUDA c10::Half instantiations
            # that libtorch_cuda requires. Build PyTorch's matching bundled Gloo.
            env.set("USE_SYSTEM_GLOO", "OFF")
