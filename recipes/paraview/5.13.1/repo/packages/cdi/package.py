# Copyright 2013-2024 Lawrence Livermore National Security, LLC and other
# Spack Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: (Apache-2.0 OR MIT)

# ----------------------------------------------------------------------------
# If you submit this package back to Spack as a pull request,
# please first remove this boilerplate and all FIXME comments.
#
# This is a template package file for Spack.  We've put "FIXME"
# next to all the things you'll want to change. Once you've handled
# them, you can save this file and test your package like this:
#
#     spack install cdi
#
# You can edit this file again by typing:
#
#     spack edit cdi
#
# See the Spack documentation for more information on packaging.
# ----------------------------------------------------------------------------

from spack.package import *


class Cdi(AutotoolsPackage):
    """
    CDI is a C and Fortran Interface to access Climate and NWP model Data.
    Supported data formats are GRIB, netCDF, SERVICE, EXTRA and IEG.
    """

    homepage = "https://code.mpimet.mpg.de/projects/cdi"
    url = "https://code.mpimet.mpg.de/attachments/download/29309/cdi-2.4.0.tar.gz"

    # FIXME: Add the SPDX identifier of the project's license below.
    # See https://spdx.org/licenses/ for a list. Upon manually verifying
    # the license, set checked_by to your Github username.
    # license("UNKNOWN", checked_by="github_user1")

    version("2.4.0", sha256="91fca015b04c6841b9eab8b49e7726d35e35b9ec4350922072ec6e9d5eb174ef")

    variant("netcdf", default=True, description="This is needed to read/write NetCDF files with CDI")

    depends_on("netcdf-c", when="+netcdf")

    def configure_args(self):
        args = []
        if "+netcdf" in self.spec:
            args.append("--with-netcdf=" + self.spec["netcdf-c"].prefix)
        return args
