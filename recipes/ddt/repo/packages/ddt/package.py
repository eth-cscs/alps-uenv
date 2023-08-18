from spack.package import *


class Ddt(Package):
    """Linaro Forge DDT Debugger"""
    homepage = "https://www.linaroforge.com/downloadForge/"
    url = "https://downloads.linaroforge.com/23.0.1/linaro-forge-23.0.1-linux-x86_64.tar"
    maintainers("jgphpc")
    license_required = False
    version(
        "23.0.1",
        url="https://downloads.linaroforge.com/23.0.1/linaro-forge-23.0.1-linux-x86_64.tar",
        sha256="1d681891c0c725363f0f45584c9b79e669d5c9782158453b7d24b4b865d72755",
    )
    version(
        "23.0",
        url="https://downloads.linaroforge.com/23.0/linaro-forge-23.0-linux-x86_64.tar",
        sha256="f4ab12289c992dd07cb1a15dd985ef4713d1f9c0cf362ec5e9c995cca9b1cf81",
    )

    def setup_run_environment(self, env):
        env.prepend_path("PATH", join_path(self.prefix, "bin"))

    def install(self, spec, prefix):
        install_shell = which("sh")
        args = ["./textinstall.sh", "--accept-license", prefix]
        install_shell(*args)

    @run_after("install")
    def post_install(self):
        cscs_licence = join_path(self.prefix, "licences", "License")
        with open(cscs_licence, "w") as f:
            # will expire end of May/2026
            f.write("type=2\n")
            f.write("serial_number=17741\n")
            f.write("hostname=velan.cscs.ch\n")
            f.write("serverport=4241\n")
            f.write("features=ddt,map,perf-report,cuda,metrics-pack\n")
            f.write("hash2=b013e17d168ebec7291c66401832d113963c0cb5\n")
