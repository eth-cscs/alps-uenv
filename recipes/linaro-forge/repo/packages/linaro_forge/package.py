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
        version("25.1", sha256="62d215e4ffd20e69863b1ffb7f043968aa7a3bf21280f5dcf2e64a2db7deb675")
        version("25.0.4", sha256="6d9a7ffcc18c6b89175167e100d80c46e2206b7a3655d6449dc63881f834b031")
    elif platform.machine() == "x86_64":
        version("25.1", sha256="153b0264939762431cb5242cd67774832c9ac9c2a2658a6918110064c322eaa1")
        version("25.0.4", sha256="ee93a414f6183165cd8addf926a4a586668ce29930f34edd43d33c750646f0be")

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
        pre = "arm" if version < Version("23.0") else "linaro"
        return f"https://downloads.linaroforge.com/{version}/{pre}-forge-{version}-linux-{platform.machine()}.tar"

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
