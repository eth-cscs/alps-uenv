from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


HELPER = Path(__file__).with_name("paseo.py")


class PaseoProfileTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.project = self.root / "project"
        self.project.mkdir()
        self.context = self.root / "context.json"
        self.selection = self.root / "selection.json"

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def prepare(self, mode: str):
        return subprocess.run(
            [sys.executable, str(HELPER), "prepare", "--home", str(self.root / "home"),
             "--profiles", str(self.root / "profiles"), "--project", str(self.project),
             "--launchers", str(self.root / "bin"), "--omp", "/bin/false",
             "--opencode", "/bin/false", "--local-storage", str(self.root / "local"),
             "--context", str(self.context), "--selection", str(self.selection),
             "--host-roots", *(str(self.root / key) for key in ("config", "data", "cache", "state")),
             "--mode", mode],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=10,
        )

    def test_existing_profile_cannot_silently_change_native_history_owner(self) -> None:
        self.assertEqual(self.prepare("isolated").returncode, 0)
        original = self.context.read_bytes()
        self.assertNotEqual(self.prepare("home").returncode, 0)
        self.assertEqual(self.context.read_bytes(), original)
        self.assertEqual(json.loads(self.selection.read_text()), {"mode": "isolated"})
        self.assertFalse((self.root / "data").exists())

    def test_project_profile_rejects_symlink_escape_before_writing_harness_data(self) -> None:
        outside = self.root / "outside"
        outside.mkdir()
        (self.project / ".cscs-agents").symlink_to(outside, target_is_directory=True)
        self.assertNotEqual(self.prepare("project:existing").returncode, 0)
        self.assertEqual(list(outside.iterdir()), [])
        self.assertFalse(self.context.exists())

    def test_resume_refuses_session_from_another_paseo_profile(self) -> None:
        self.assertEqual(self.prepare("isolated").returncode, 0)
        foreign = self.root / "foreign.jsonl"
        foreign.write_text('{"id":"another-owner"}\n')
        result = subprocess.run(
            [sys.executable, str(HELPER), "provider", "omp", "--", "--mode", "rpc-ui", "--session", str(foreign)],
            env={**os.environ, "CSCS_PASEO_CONTEXT": str(self.context)},
            cwd=self.project, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=10,
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(foreign.read_text(), '{"id":"another-owner"}\n')
        self.assertFalse((self.root / "profiles" / "omp" / "foreign.jsonl").exists())


if __name__ == "__main__":
    unittest.main()
