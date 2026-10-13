from __future__ import annotations

import json
import os
import shlex
import stat
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


PACKAGE_DIR = Path(__file__).parent
RECIPE_DIR = PACKAGE_DIR.parents[2]
TEMPLATE = PACKAGE_DIR / "agent-bwrap.in"
STORAGE = PACKAGE_DIR / "storage.py"
MODEL_DEFAULTS = RECIPE_DIR / "repo/packages/cscs_agent_model_config/files"
LAUNCHER_DEFAULTS = PACKAGE_DIR / "files"


def executable(path: Path, content: str) -> None:
    path.write_text(content)
    path.chmod(path.stat().st_mode | stat.S_IXUSR)


class LauncherArgumentsTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.bin = self.root / "bin"
        self.bin.mkdir()
        self.capture = self.root / "bwrap.json"

        fake_agent = self.bin / "agent"
        executable(fake_agent, "#!/bin/sh\nexit 0\n")
        fake_bwrap = self.bin / "bwrap"
        executable(
            fake_bwrap,
            "#!/bin/sh\n"
            f"exec {shlex.quote(sys.executable)} -c "
            + shlex.quote(
                "import json,os,sys; "
                "open(os.environ['BWRAP_CAPTURE'], 'w').write(json.dumps(sys.argv[1:]))"
            )
            + ' "$@"\n',
        )

        tools = self.root / "tools"
        self.python_version = f"{sys.version_info.major}.{sys.version_info.minor}"
        python_install = tools / f"python/{self.python_version}/cpython-test/bin"
        python_bin = tools / f"python-bin/{self.python_version}"
        uv_bin = tools / "uv/0.12.7"
        for directory in (tools / "bin", python_install, python_bin, uv_bin):
            directory.mkdir(parents=True, exist_ok=True)
        python_wrapper = python_install / "python3"
        executable(
            python_wrapper,
            f"#!/bin/sh\nexec {shlex.quote(sys.executable)} \"$@\"\n",
        )
        (python_bin / "python3").symlink_to(python_wrapper)
        (python_bin / "python").symlink_to(python_wrapper)
        executable(uv_bin / "uv", "#!/bin/sh\nprintf 'uv 0.12.7 (test)\\n'\n")
        (python_bin / ".ready").write_text("test\n")
        self.tools = tools

        replacements = {
            "@OPENCODE@": str(fake_agent),
            "@OMP@": str(fake_agent),
            "@PRIME_AGENT@": str(fake_agent),
            "@BWRAP@": str(fake_bwrap),
            "@CSCS_MODEL_CONFIG@": "/bin/false",
            "@CSCS_MODEL_DEFAULTS@": str(MODEL_DEFAULTS),
            "@LAUNCHER_DEFAULTS@": str(LAUNCHER_DEFAULTS),
            "@STORAGE_HELPER@": str(STORAGE),
            "@CSCS_SKILLS@": str(self.root / "no-skills"),
            "@OPENCODE_BIN@": str(self.bin),
            "@OMP_BIN@": str(self.bin),
            "@PRIME_AGENT_BIN@": str(self.bin),
            "@RIPGREP_BIN@": str(self.bin),
            "@CRUN_BIN@": str(fake_agent),
            "@CATATONIT_BIN@": str(fake_agent),
            "@FUSE_OVERLAYFS_BIN@": str(fake_agent),
        }
        launcher = TEMPLATE.read_text()
        for token, value in replacements.items():
            launcher = launcher.replace(token, value)
        self.launchers = {}
        for name in ("opencode-bwrap", "omp-bwrap", "prime-agent-bwrap"):
            target = self.bin / name
            executable(target, launcher)
            self.launchers[name] = target

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def run_launcher(self, name: str, command: list[str] | None = None) -> tuple[list[str], dict[str, Path]]:
        roots = {
            key: self.root / name / key
            for key in ("project", "config", "data", "cache", "state", "local")
        }
        roots["project"].mkdir(parents=True)
        environment = {
            **os.environ,
            "BWRAP_CAPTURE": str(self.capture),
            "CSCS_AGENT_LOCAL_STORAGE_DIR": str(roots["local"]),
            "CSCS_AGENT_PYTHON_VERSION": self.python_version,
            "CSCS_AGENT_TOOLS_DIR": str(self.tools),
            "CSCS_AGENT_TOOLS_CACHE_DIR": str(self.root / "tools-cache"),
            "HOME": str(self.root / "home"),
        }
        for variable in (
            "CSCS_API_KEY",
            "CSCS_INFERENCE_API_KEY",
            "CSCS_INFERENCE_API_KEY_FORNO",
        ):
            environment.pop(variable, None)
        arguments = [
            str(self.launchers[name]),
            "--project-dir", str(roots["project"]),
            "--config-dir", str(roots["config"]),
            "--data-dir", str(roots["data"]),
            "--cache-dir", str(roots["cache"]),
            "--state-dir", str(roots["state"]),
            "--no-default-hide-paths",
            "--",
            *(command or []),
        ]
        subprocess.run(arguments, env=environment, check=True, timeout=30)
        return json.loads(self.capture.read_text()), roots

    @staticmethod
    def setenv(arguments: list[str], name: str) -> str:
        for index, argument in enumerate(arguments[:-2]):
            if argument == "--setenv" and arguments[index + 1] == name:
                return arguments[index + 2]
        raise AssertionError(f"missing --setenv {name}")

    def test_default_profiles_are_release_versioned(self) -> None:
        stems = {
            "opencode-bwrap": "opencode-cscs-agents-26.10",
            "omp-bwrap": "omp-cscs-agents-26.10",
            "prime-agent-bwrap": "prime-agent-cscs-agents-26.10",
        }
        environment = {
            **os.environ,
            "HOME": str(self.root / "home"),
            "XDG_CONFIG_HOME": str(self.root / "xdg-config"),
            "XDG_DATA_HOME": str(self.root / "xdg-data"),
            "XDG_CACHE_HOME": str(self.root / "xdg-cache"),
            "XDG_STATE_HOME": str(self.root / "xdg-state"),
        }
        for name, stem in stems.items():
            result = subprocess.run(
                [str(self.launchers[name]), "--help"],
                env=environment,
                stdout=subprocess.PIPE,
                text=True,
                check=True,
            )
            for root in ("xdg-config", "xdg-data", "xdg-cache", "xdg-state"):
                self.assertIn(str(self.root / root / stem), result.stdout)

    def test_opencode_database_is_node_local(self) -> None:
        arguments, roots = self.run_launcher("opencode-bwrap")
        database = Path(self.setenv(arguments, "OPENCODE_DB"))
        self.assertTrue(database.is_relative_to(roots["local"]))
        self.assertFalse(database.is_relative_to(roots["data"]))
        for variable in ("CSCS_AGENT_STORAGE_CHILD", "CSCS_AGENT_MAINTENANCE_CHILD"):
            index = arguments.index(variable)
            self.assertEqual(arguments[index - 1], "--unsetenv")

    def test_omp_xdg_and_natives_are_node_local(self) -> None:
        arguments, roots = self.run_launcher("omp-bwrap")
        for variable in ("XDG_DATA_HOME", "XDG_CACHE_HOME", "XDG_STATE_HOME"):
            self.assertTrue(Path(self.setenv(arguments, variable)).is_relative_to(roots["local"]))
        self.assertTrue(
            Path(self.setenv(arguments, "PI_NATIVES_DIR")).is_relative_to(roots["local"])
        )
        self.assertIn("PI_CODING_AGENT_DIR", arguments)

    def test_prime_uses_models_json_and_local_runtime_overlays(self) -> None:
        arguments, roots = self.run_launcher("prime-agent-bwrap", ["model", "list"])
        agent_dir = roots["config"] / "home/.prime/agent"
        models = json.loads((agent_dir / "models.json").read_text())
        self.assertIn("cscs", models["providers"])
        self.assertFalse((agent_dir / "extensions/cscs-provider.ts").exists())
        tmpdir = Path(self.setenv(arguments, "TMPDIR"))
        self.assertIn("prime-agent", tmpdir.name)
        self.assertIn("prime-agent-", str(self.setenv(arguments, "XDG_RUNTIME_DIR")))

        for destination in (agent_dir / "session-leases", agent_dir / "daemon-workers"):
            final = arguments.index(str(destination))
            source = Path(arguments[final - 1])
            self.assertTrue(source.is_relative_to(roots["local"]))
            self.assertEqual(arguments[final - 2], "--bind")
            self.assertGreater(final, max(
                index for index, value in enumerate(arguments) if value == str(roots["config"])
            ))

    def test_ambient_internal_mode_is_rejected(self) -> None:
        environment = {
            **os.environ,
            "CSCS_AGENT_STORAGE_CHILD": "1",
        }
        result = subprocess.run(
            [str(self.launchers["opencode-bwrap"]), "--help"],
            env=environment,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=False,
        )
        self.assertEqual(result.returncode, 1)
        self.assertIn("not started by the profile storage supervisor", result.stderr)


if __name__ == "__main__":
    unittest.main()
