# Copyright Spack Project Developers. See COPYRIGHT file for details.
#
# SPDX-License-Identifier: (Apache-2.0 OR MIT)

from spack_repo.builtin.build_systems.generic import Package

from spack.package import *


class Paseo(Package):
    """Paseo CLI, daemon and served web UI from published npm packages.

    package.json retains the release's production dependencies but omits its
    development dependencies and lifecycle scripts. Regenerate package-lock.json
    with the pinned npm CLI using install --package-lock-only --ignore-scripts
    --omit=dev --include=optional --no-audit --no-fund in an empty directory.
    The shared lock contains optional binaries for both supported architectures;
    npm ci selects the native packages without compiling or running scripts.
    """

    homepage = "https://github.com/getpaseo/paseo"
    url = "https://registry.npmjs.org/@getpaseo/cli/-/cli-0.12.0.tgz"

    license("Apache-2.0")

    version(
        "0.12.0",
        sha256="51843851f5a9c14f7b22d2c6c4970357ff602781c1bddfd9c97de55cc03b5aa3",
    )

    # The npm release omits LICENSE. Pin its matching gitHead, not a moving tag.
    resource(
        name="license",
        url="https://raw.githubusercontent.com/getpaseo/paseo/"
        "cafe4b01c8522ff39560241c5deb01427dc8dc5b/LICENSE",
        sha256="79d5aedce6aa0adc547336dc1bd34c5cc9308ba110fac7079ed97515ee573ad3",
        expand=False,
        destination="license",
        placement={"LICENSE": "LICENSE"},
    )

    # Spack node-js deliberately omits npm. Never use a host npm or Node.
    resource(
        name="npm",
        url="https://registry.npmjs.org/npm/-/npm-10.9.4.tgz",
        sha256="4bfba8a0c823024d1926ec9d97a37a00eb60fd2adf44b3d34a686fc32e8f51e4",
        destination="npm",
        placement="cli",
    )

    depends_on("node-js@22.22.2", type=("build", "run"))

    phases = ["install"]

    sanity_check_is_file = [
        "bin/paseo",
        "libexec/paseo/bin/paseo",
        "libexec/paseo/dist/index.js",
        "libexec/paseo/node_modules/@getpaseo/server/dist/scripts/supervisor-entrypoint.js",
        "libexec/paseo/node_modules/@getpaseo/server/dist/server/server/exports.js",
        "libexec/paseo/node_modules/@getpaseo/server/dist/server/web-ui/index.html",
        "share/licenses/paseo/LICENSE",
    ]

    def content_hash(self, content=None):
        if content is None:
            with open(join_path(self.package_dir, "package.py"), "rb") as f:
                content = f.read()

        for name in ("package.json", "package-lock.json"):
            with open(join_path(self.package_dir, name), "rb") as f:
                content += b"\n_paseo_input = " + repr((name, f.read())).encode("utf-8") + b"\n"

        return super().content_hash(content=content)

    def setup_build_environment(self, env):
        env.set("HOME", self.stage.path)
        env.set("NPM_CONFIG_USERCONFIG", "/dev/null")
        env.set("NPM_CONFIG_GLOBALCONFIG", join_path(self.stage.path, "npm-globalrc"))
        env.set("NPM_CONFIG_UPDATE_NOTIFIER", "false")
        env.set("npm_config_cache", join_path(self.stage.path, "npm-cache"))

    def install(self, spec, prefix):
        if not spec.satisfies("platform=linux"):
            raise InstallError("paseo only packages published Linux arm64 and x86_64 runtimes")
        if spec.satisfies("target=aarch64:"):
            arch = "arm64"
        elif spec.satisfies("target=x86_64:"):
            arch = "x64"
        else:
            raise InstallError("paseo only packages published Linux arm64 and x86_64 runtimes")

        for name in ("package.json", "package-lock.json"):
            install(join_path(self.package_dir, name), self.stage.source_path)

        npm_cli = join_path(self.stage.source_path, "npm", "cli", "bin", "npm-cli.js")
        Executable(spec["node-js"].prefix.bin.node)(
            npm_cli,
            "ci",
            "--ignore-scripts",
            "--omit=dev",
            "--include=optional",
            "--no-audit",
            "--no-fund",
        )

        app = join_path(prefix.libexec, "paseo")
        mkdirp(app, prefix.bin)
        for directory in ("bin", "dist", "node_modules"):
            install_tree(directory, join_path(app, directory))
        for name in ("package.json", "package-lock.json"):
            install(name, app)

        # node-pty loads these published N-API binaries directly; its lifecycle
        # scripts are deliberately skipped, including their node-gyp fallback.
        self.sanity_check_is_file = list(self.sanity_check_is_file) + [
            "libexec/paseo/node_modules/node-pty/prebuilds/linux-{0}/pty.node".format(arch),
            "libexec/paseo/node_modules/@esbuild/linux-{0}/bin/esbuild".format(arch),
        ]

        license_dir = join_path(prefix.share, "licenses", "paseo")
        mkdirp(license_dir)
        install(join_path("license", "LICENSE"), license_dir)

        launcher = join_path(prefix.bin, "paseo")
        with open(launcher, "w", encoding="utf-8") as f:
            f.write("#!/bin/sh\n")
            f.write(
                'exec "{0}" --disable-warning=DEP0040 "{1}" "$@"\n'.format(
                    spec["node-js"].prefix.bin.node,
                    join_path(app, "bin", "paseo"),
                )
            )
        set_executable(launcher)
