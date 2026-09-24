# Copyright Spack Project Developers. See COPYRIGHT file for details.
#
# SPDX-License-Identifier: (Apache-2.0 OR MIT)

from spack_repo.builtin.packages.ucc.package import Ucc as BuiltinUcc


class Ucc(BuiltinUcc):
    """Collective communication operations API and library."""

    def configure_args(self):
        args = super().configure_args()
        return [
            arg.replace("--generate-code ", "-gencode=")
            if arg.startswith("--with-nvcc-gencode=")
            else arg
            for arg in args
        ]
