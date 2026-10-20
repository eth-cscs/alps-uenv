from __future__ import annotations

import json
import os
import shlex
import stat
import sqlite3
import subprocess
import sys
import tempfile
import time
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

    def launcher_invocation(
        self,
        name: str,
        command: list[str] | None = None,
        *,
        environment_overrides: dict[str, str] | None = None,
        options: list[str] | None = None,
        project_dir: Path | None = None,
        project_local: bool = False,
        instance: str | None = None,
    ) -> tuple[list[str], dict[str, str], dict[str, Path]]:
        roots = {
            key: self.root / name / key
            for key in ("project", "config", "data", "cache", "state", "local")
        }
        roots["project"].mkdir(parents=True, exist_ok=True)
        if project_dir is not None:
            roots["project"] = project_dir
            project_dir.mkdir(parents=True, exist_ok=True)
        if project_local:
            namespace = "opencode-v2" if name == "opencode-bwrap" else name.removesuffix("-bwrap")
            profile = roots["project"] / ".cscs-agents/26.10" / namespace / (instance or "default")
            for key in ("config", "data", "cache", "state"):
                roots[key] = profile / key
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
        environment.update(environment_overrides or {})
        arguments = [
            str(self.launchers[name]),
            "--project-dir", str(roots["project"]),
            "--no-default-hide-paths",
        ]
        if project_local:
            arguments.append("--project-local")
        else:
            for key in ("config", "data", "cache", "state"):
                arguments.extend([f"--{key}-dir", str(roots[key])])
        if instance is not None:
            arguments.extend(["--instance", instance])
        arguments.extend([*(options or []), "--", *(command or [])])
        return arguments, environment, roots

    def run_launcher(self, name: str, command: list[str] | None = None, **kwargs):
        arguments, environment, roots = self.launcher_invocation(name, command, **kwargs)
        subprocess.run(
            arguments, env=environment, check=True, timeout=30,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
        )
        return json.loads(self.capture.read_text()), roots

    @staticmethod
    def setenv(arguments: list[str], name: str) -> str:
        for index, argument in enumerate(arguments[:-2]):
            if argument == "--setenv" and arguments[index + 1] == name:
                return arguments[index + 2]
        raise AssertionError(f"missing --setenv {name}")


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

    def test_network_tools_and_cache_are_rejected_before_launch(self) -> None:
        for variable, filesystem in (
            ("CSCS_AGENT_TOOLS_DIR", "nfs"),
            ("CSCS_AGENT_TOOLS_CACHE_DIR", "lustre"),
        ):
            with self.subTest(variable=variable):
                network_path = self.root / variable
                executable(
                    self.bin / "stat",
                    f"#!{sys.executable}\n"
                    "import os, sys\n"
                    f"if sys.argv[1:] == ['-f', '-c', '%T', {str(network_path)!r}]:\n"
                    f"    print({filesystem!r})\n"
                    "else:\n"
                    "    os.execv('/usr/bin/stat', ['stat', *sys.argv[1:]])\n",
                )
                with self.assertRaises(subprocess.CalledProcessError) as caught:
                    self.run_launcher(
                        "opencode-bwrap",
                        environment_overrides={
                            variable: str(network_path),
                            "PATH": f"{self.bin}:{os.environ['PATH']}",
                        },
                    )
                self.assertIn(f"cannot use {filesystem}", caught.exception.stderr)
                self.assertIn(str(network_path), caught.exception.stderr)
                self.assertFalse(self.capture.exists())

    def test_symlinked_tools_directory_is_rejected(self) -> None:
        link = self.root / "tools-link"
        link.symlink_to(self.tools, target_is_directory=True)
        with self.assertRaises(subprocess.CalledProcessError) as caught:
            self.run_launcher(
                "opencode-bwrap",
                environment_overrides={"CSCS_AGENT_TOOLS_DIR": str(link)},
            )
        self.assertIn("tools directory must not be a symlink", caught.exception.stderr)
        self.assertFalse(self.capture.exists())

    def test_extra_bind_cannot_mask_tools_or_cache(self) -> None:
        for target in (self.tools, self.root / "tools-cache"):
            with self.subTest(target=target):
                with self.assertRaises(subprocess.CalledProcessError) as caught:
                    self.run_launcher(
                        "opencode-bwrap",
                        options=["--bind", f"{self.bin}:{target}"],
                    )
                self.assertIn("overlaps protected node-local", caught.exception.stderr)
                self.assertFalse(self.capture.exists())

    def test_project_instances_preserve_independent_settings(self) -> None:
        for name in self.launchers:
            with self.subTest(harness=name):
                command = ["model", "list"] if name == "prime-agent-bwrap" else []
                first, roots = self.run_launcher(
                    name, command, project_local=True, instance="implementer",
                )
                marker = roots["config"] / "user-settings"
                marker.write_text("implementer-only")
                second, other = self.run_launcher(
                    name, command, project_local=True, instance="reviewer",
                )
                self.assertFalse((other["config"] / "user-settings").exists())
                self.assertNotEqual(
                    self.setenv(first, "XDG_RUNTIME_DIR"),
                    self.setenv(second, "XDG_RUNTIME_DIR"),
                )
                self.run_launcher(name, command, project_local=True, instance="implementer")
                self.assertEqual(marker.read_text(), "implementer-only")

    def test_project_profile_credentials_are_git_ignored(self) -> None:
        project = self.root / "git-project"
        subprocess.run(["git", "init", "--quiet", str(project)], check=True)
        _, roots = self.run_launcher(
            "opencode-bwrap", project_dir=project, project_local=True,
        )
        credentials = roots["config"] / "credentials.json"
        credentials.write_text('{"token": "test-only"}\n')
        ignored = subprocess.run(
            ["git", "-C", str(project), "check-ignore", "--quiet", str(credentials)],
        )
        self.assertEqual(ignored.returncode, 0)
        project_file = project / "main.py"
        project_file.write_text("pass\n")
        not_ignored = subprocess.run(
            ["git", "-C", str(project), "check-ignore", "--quiet", str(project_file)],
        )
        self.assertEqual(not_ignored.returncode, 1)

    def test_project_profiles_do_not_follow_symlinks(self) -> None:
        project = self.root / "project-symlink"
        project.mkdir()
        elsewhere = self.root / "outside"
        elsewhere.mkdir()
        (project / ".cscs-agents").symlink_to(elsewhere, target_is_directory=True)
        with self.assertRaises(subprocess.CalledProcessError):
            self.run_launcher("opencode-bwrap", project_dir=project, project_local=True)
        self.assertEqual(list(elsewhere.iterdir()), [])

    def test_invalid_project_profile_options_are_rejected_without_creating_state(self) -> None:
        cases = (
            {"instance": "reviewer"},
            {"project_local": True, "instance": "../escape"},
            {"project_local": True, "instance": "/absolute"},
            {"project_local": True, "options": ["--data-dir", str(self.root / "override")]},
            {"project_local": True, "options": ["--config-dir=" + str(self.root / "override")]},
        )
        for options in cases:
            with self.subTest(options=options):
                with self.assertRaises(subprocess.CalledProcessError):
                    self.run_launcher("opencode-bwrap", **options)
        self.assertFalse((self.root / "opencode-bwrap/project/.cscs-agents").exists())
        self.assertFalse((self.root / "override").exists())
        self.assertFalse(self.capture.exists())

    def test_concurrent_profiles_checkpoint_separately_and_reject_duplicate_writer(self) -> None:
        executable(
            self.bin / "bwrap",
            f"#!{sys.executable}\n"
            "import json, os, sqlite3, sys, time\n"
            "from pathlib import Path\n"
            "args = sys.argv[1:]\n"
            "env = {args[i+1]: args[i+2] for i, value in enumerate(args) if value == '--setenv'}\n"
            "db = Path(env['OPENCODE_DB']) if 'OPENCODE_DB' in env else Path(env['XDG_DATA_HOME'])/'omp/probe.db'\n"
            "connection = sqlite3.connect(db)\n"
            "connection.execute('create table probe(value text)')\n"
            "connection.execute('insert into probe values (?)', (os.environ['PROFILE_VALUE'],))\n"
            "connection.commit()\n"
            "Path(os.environ['PROFILE_READY']).write_text(str(db))\n"
            "while not Path(os.environ['PROFILE_RELEASE']).exists():\n"
            "    time.sleep(0.02)\n"
            "connection.close()\n",
        )
        for name in ("opencode-bwrap", "omp-bwrap"):
            with self.subTest(harness=name):
                release = self.root / f"{name}.release"
                children = []
                profiles = []
                try:
                    for index, (project, instance) in enumerate((
                        ("project-a", "implementer"),
                        ("project-a", "reviewer"),
                        ("project-b", "implementer"),
                    )):
                        ready = self.root / f"{name}-{index}.ready"
                        arguments, environment, roots = self.launcher_invocation(
                            name, project_local=True, instance=instance,
                            project_dir=self.root / project,
                            environment_overrides={
                                "PROFILE_VALUE": str(index),
                                "PROFILE_READY": str(ready),
                                "PROFILE_RELEASE": str(release),
                            },
                        )
                        child = subprocess.Popen(
                            arguments, env=environment, stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE, text=True,
                        )
                        children.append(child)
                        profiles.append((roots, ready))
                        deadline = time.monotonic() + 15
                        while not ready.exists():
                            if child.poll() is not None:
                                self.fail(f"launcher exited: {child.communicate()}")
                            if time.monotonic() >= deadline:
                                self.fail("launcher did not reach the supervised writer")
                            time.sleep(0.02)

                    arguments, environment, _ = self.launcher_invocation(
                        name, project_local=True, instance="implementer",
                        project_dir=self.root / "project-a",
                    )
                    duplicate = subprocess.run(
                        arguments, env=environment, capture_output=True, text=True, timeout=10,
                    )
                    self.assertNotEqual(duplicate.returncode, 0)
                    self.assertIn("profile is already owned", duplicate.stderr)
                    self.assertTrue(all(child.poll() is None for child in children))
                    release.touch()
                    for child in children:
                        _, error = child.communicate(timeout=15)
                        self.assertEqual(child.returncode, 0, error)

                    for index, (roots, ready) in enumerate(profiles):
                        database = Path(ready.read_text())
                        relative_db = (
                            Path("opencode.db") if name == "opencode-bwrap" else Path("data/probe.db")
                        )
                        store = (
                            roots["data"] / ".cscs-agent-storage"
                            / ("opencode-v2" if name == "opencode-bwrap" else "omp")
                        )
                        generation = (store / "current").read_text().strip()
                        checkpoint = store / "generations" / generation / relative_db
                        for saved in (database, checkpoint):
                            with sqlite3.connect(saved) as connection:
                                self.assertEqual(
                                    connection.execute("select value from probe").fetchall(),
                                    [(str(index),)],
                                )
                finally:
                    release.touch()
                    for child in children:
                        if child.poll() is None:
                            child.terminate()
                        child.communicate(timeout=15)

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
