# Copyright Spack Project Developers. See COPYRIGHT file for details.
#
# SPDX-License-Identifier: (Apache-2.0 OR MIT)

from spack_repo.builtin.build_systems.python import PythonPackage

from spack.package import *

import glob

class PyHfXet(PythonPackage):
    """Fast transfer of large files with the Hugging Face Hub."""

    pypi = "hf-xet/hf_xet-1.1.5.tar.gz"

    license("Apache-2.0")

    version("1.2.0", sha256="a8c27070ca547293b6890c4bf389f713f80e8c478631432962bb7f4bc0bd7d7f")
    version("1.1.5", sha256="69ebbcfd9ec44fdc2af73441619eeb06b94ee34511bbcf57cd423820090f5694")

    depends_on("c", type="build")
    depends_on("cxx", type="build")

    # https://github.com/huggingface/xet-core/blob/v1.1.5/hf_xet/pyproject.toml
    depends_on("py-maturin@1.7:1", type="build")

    def patch(self):
        with working_dir(self.stage.source_path):
            tomls = glob.glob("**/Cargo.toml", recursive=True)
            for path in tomls:
                filter_file(
                    r'(sha2\s*=\s*\{[^}]*features\s*=\s*)\[\s*"?asm"?\s*\](\s*\})',
                    r'\1[]\2',
                    path,
                    ignore_absent=True,
                )
