# Copyright Spack Project Developers. See COPYRIGHT file for details.
#
# SPDX-License-Identifier: (Apache-2.0 OR MIT)

import os
import platform
import subprocess

from spack_repo.builtin.build_systems.generic import Package

from spack.package import *


class LinaroForge(Package):
    """Build reliable and optimized code for the right results on multiple
    Server and HPC architectures, from the latest compilers and C++ standards
    to Intel, 64-bit Arm, AMD, OpenPOWER and Nvidia GPU hardware. Linaro Forge
    combines Linaro DDT, the leading debugger for time-saving high performance
    application debugging, Linaro MAP, the trusted performance profiler for
    invaluable optimization advice across native and Python HPC codes, and
    Linaro Performance Reports for advanced reporting capabilities."""

    homepage = "https://www.linaroforge.com"
    maintainers("kenche-linaro")

    if platform.machine() == "aarch64":
        version("26.0", sha256="e1510c0377bbc49821ba9758c8ed5563fe3e08dc072860319ea0ac5cb088c7c8")
        version("25.1.2", sha256="4bd7928dae0d9e3f01c6cecc671ad31b957731a1f137c81993b7b20373c5623d")
    elif platform.machine() == "x86_64":
        version("26.0", sha256="060b44e014b13632f1d56386acd3bbbbd7d07b5033dbb2af264bd91c5ac23e1e")
        version("25.1.2", sha256="277f810b6cb52428a10c3317d07d0887140b8dbe5269485ba6715e23be3b55bb")

    variant(
        "probe",
        default=False,
        description='Detect available PMU counters via "forge-probe" during install',
    )

    variant("accept-eula", default=False, description="Accept the EULA")

    # forge-probe executes with "/usr/bin/env python"
    depends_on("python@2.7:", type="build", when="+probe")

    # Licensing
    license_required = False

    def url_for_version(self, version):
        return f"https://downloads.linaroforge.com/{version}/linaro-forge-{version}-linux-{platform.machine()}.tar"

    @run_before("install")
    def abort_without_eula_acceptance(self):
        install_example = "spack install linaro-forge +accept-eula"
        license_terms_path = os.path.join(self.stage.source_path, "license_terms")
        if not self.spec.variants["accept-eula"].value:
            raise InstallError(
                "\n\n\nNOTE:\nUse +accept-eula "
                + "during installation "
                + "to accept the license terms in:\n"
                + "  {0}\n".format(os.path.join(license_terms_path, "license_agreement.txt"))
                + "  {0}\n\n".format(os.path.join(license_terms_path, "supplementary_terms.txt"))
                + "Example: '{0}'\n".format(install_example)
            )

    def install(self, spec, prefix):
        subprocess.call(["./textinstall.sh", "--accept-license", prefix])
        if spec.satisfies("+probe"):
            probe = join_path(prefix, "bin", "forge-probe")
            subprocess.call([probe, "--install", "global"])

    def setup_run_environment(self, env: EnvironmentModifications) -> None:
        # Only PATH is needed for Forge.
        # Adding lib to LD_LIBRARY_PATH can cause conflicts with Forge's internal libs.
        env.clear()
        env.prepend_path("PATH", join_path(self.prefix, "bin"))

    @run_after("install")
    def cscs_license(self):
        cscs_license = join_path(self.prefix, "licences", "License")
        with open(cscs_license, "w") as f:
            # will expire end of May/2026
            f.write("type=2\n")
            f.write("serial_number=17741\n")
            f.write("hostname=velan.cscs.ch\n")
            f.write("serverport=4241\n")
            f.write("features=ddt,map,perf-report,cuda,metrics-pack\n")
            f.write("hash2=b013e17d168ebec7291c66401832d113963c0cb5\n")
