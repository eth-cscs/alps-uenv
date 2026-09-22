# Copyright Spack Project Developers. See COPYRIGHT file for details.
#
# SPDX-License-Identifier: (Apache-2.0 OR MIT)

import os

from spack_repo.builtin.build_systems.autotools import AutotoolsPackage

from spack.package import *


class Crun(AutotoolsPackage):
    """OCI runtime, patched for CSCS agent sandboxes.

    Stock crun mounts /dev/pts with gid=5 (the host `tty` group) whenever the
    calling process has euid 0. In a user namespace that only maps a single
    gid, gid 5 is unmappable and the kernel rejects the mount with EINVAL,
    so rootful podman inside `unshare -Ur`-style sandboxes cannot start any
    container. The carried patch omits gid=5 whenever gid 5 is not covered
    by the current /proc/self/gid_map, matching what the rootless branch has
    always done; normal hosts keep the stock behavior.
    """

    homepage = "https://github.com/containers/crun"
    url = "https://github.com/containers/crun/releases/download/1.29.1/crun-1.29.1.tar.gz"

    license("GPL-2.0-or-later")

    version(
        "1.29.1",
        sha256="b6be9fd9613efe5df414c568ddfaf09857c72ec17a00999f15c132a3d9e120fd",
    )

    depends_on("c", type="build")  # generated

    depends_on("json-c", type=("build", "link"))
    depends_on("libseccomp", type=("build", "link"))
    depends_on("libcap", type=("build", "link"))

    # Upstream optional integrations (systemd, CRIU, wasm runtimes, language
    # bindings) add heavy dependencies and are irrelevant for a sandbox
    # runtime. The release tarball ships a pre-generated configure script,
    # so no autoreconf is needed.
    def configure_args(self):
        return [
            "--disable-systemd",
            "--disable-criu",
            "--without-wasmer",
            "--without-wasmtime",
            "--without-wasmedge",
            "--without-wamr",
            "--without-libkrun",
            "--without-python-bindings",
            "--without-lua-bindings",
        ]

    patch("devpts-gid.patch", when="@1.29.1")

    def content_hash(self, content=None):
        """Extend the hash with the carried patch so a patch change
        invalidates same-version builds pushed to the build cache."""
        if content is None:
            with open(join_path(self.package_dir, "package.py"), "rb") as f:
                content = f.read()

        patch_path = join_path(self.package_dir, "devpts-gid.patch")
        if os.path.exists(patch_path):
            with open(patch_path, "rb") as f:
                content += b"\n_cscs_crun_patch = " + repr(f.read()).encode("utf-8") + b"\n"

        return super().content_hash(content=content)

    sanity_check_is_file = ["bin/crun"]
