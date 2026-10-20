# Copyright Spack Project Developers. See COPYRIGHT file for details.
#
# SPDX-License-Identifier: (Apache-2.0 OR MIT)

from spack_repo.builtin.build_systems.generic import Package

from spack.package import *


class PrimeAgent(Package):
    """Prime Agent is a terminal coding agent with persistent background workers."""

    homepage = "https://github.com/PrimeIntellect-ai/prime-agent"
    url = "https://github.com/PrimeIntellect-ai/prime-agent/archive/refs/tags/v0.9.4.tar.gz"
    supplier = "Organization: Prime Intellect"

    license("Apache-2.0")

    version(
        "0.9.4",
        sha256="db4193f529ef781eb317927e60f0cbe195c8a26434d335fc5a2e24414ebe0f76",
    )

    # Spack's node-js package deliberately configures Node with --without-npm.
    # Pin the self-contained npm CLI tarball instead of depending on a host npm.
    resource(
        name="npm",
        url="https://registry.npmjs.org/npm/-/npm-10.9.4.tgz",
        sha256="4bfba8a0c823024d1926ec9d97a37a00eb60fd2adf44b3d34a686fc32e8f51e4",
        destination="npm",
        placement="cli",
    )

    depends_on("node-js@22.12:22", type=("build", "run"))

    phases = ["build", "install"]

    sanity_check_is_file = [
        "bin/prime-agent",
        "libexec/prime-agent/packages/coding-agent/dist/bundle/cli.js",
    ]

    def setup_build_environment(self, env):
        env.set("HOME", self.stage.path)
        env.set("HUSKY", "0")
        env.set("NPM_CONFIG_AUDIT", "false")
        env.set("NPM_CONFIG_FUND", "false")
        env.set("NPM_CONFIG_UPDATE_NOTIFIER", "false")
        env.set("npm_config_cache", join_path(self.stage.path, "npm-cache"))
        env.prepend_path("PATH", join_path(self.stage.path, "npm-bin"))

    def build(self, spec, prefix):
        npm_bin = join_path(self.stage.path, "npm-bin")
        npm_cli = join_path(self.stage.source_path, "npm", "cli", "bin", "npm-cli.js")
        npm = join_path(npm_bin, "npm")
        mkdirp(npm_bin)
        with open(npm, "w", encoding="utf-8") as f:
            f.write("#!/bin/sh\n")
            f.write(
                'exec "{0}" "{1}" "$@"\n'.format(
                    spec["node-js"].prefix.bin.node,
                    npm_cli,
                )
            )
        set_executable(npm)

        Executable(npm)("ci", "--no-audit", "--no-fund")
        Executable(npm)("run", "build")

    def install(self, spec, prefix):
        app = join_path(prefix.libexec, "prime-agent")
        package = join_path(app, "packages", "coding-agent")
        modules = join_path(app, "node_modules")

        mkdirp(package, modules, prefix.bin)
        install_tree(join_path("packages", "coding-agent", "docs"), join_path(package, "docs"))
        license_dir = join_path(prefix.share, "licenses", "prime-agent")
        mkdirp(license_dir)
        install("LICENSE", license_dir)
        install_tree(join_path("packages", "coding-agent", "dist"), join_path(package, "dist"))
        install(join_path("packages", "coding-agent", "package.json"), package)

        # The bundled CLI intentionally leaves these native/runtime packages external.
        install_tree(join_path("node_modules", "koffi"), join_path(modules, "koffi"))
        install_tree(join_path("node_modules", "undici"), join_path(modules, "undici"))
        install_tree(
            join_path("node_modules", "@mariozechner"),
            join_path(modules, "@mariozechner"),
        )
        install_tree(
            join_path("node_modules", "@silvia-odwyer"),
            join_path(modules, "@silvia-odwyer"),
        )

        launcher = join_path(prefix.bin, "prime-agent")
        with open(launcher, "w", encoding="utf-8") as f:
            f.write("#!/bin/sh\n")
            f.write(
                'exec "{0}" "{1}" "$@"\n'.format(
                    spec["node-js"].prefix.bin.node,
                    join_path(package, "dist", "bundle", "cli.js"),
                )
            )
        set_executable(launcher)

    def setup_run_environment(self, env):
        env.set("PI_SKIP_VERSION_CHECK", "1")
