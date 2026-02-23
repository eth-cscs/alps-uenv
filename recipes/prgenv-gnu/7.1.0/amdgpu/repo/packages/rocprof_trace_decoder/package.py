from spack.package import *

class RocprofTraceDecoder(Package):
    """rocprof-trace-decoder: ROCm trace decoder tool."""

    homepage = "https://github.com/ROCm/rocprof-trace-decoder"
    url      = "https://github.com/ROCm/rocprof-trace-decoder/releases/download/0.1.6/rocprof-trace-decoder-manylinux-2.28-0.1.6-Linux.tar.gz"

    version("2.28-0.1.6", sha256="57a49c74db7dcd29433888ef5d408ca8e22223f2680c566855e4c3c68da7b36d")

    def install(self, spec, prefix):
       install_tree('opt/rocm/lib', self.prefix.lib)
