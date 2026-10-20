import json
import os
import signal
import sqlite3
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path
from unittest import mock

import storage


def create_database(path: Path, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(path)
    try:
        connection.execute("PRAGMA journal_mode=WAL")
        connection.execute("CREATE TABLE IF NOT EXISTS values_table (value TEXT NOT NULL)")
        connection.execute("INSERT INTO values_table VALUES (?)", (value,))
        connection.commit()
    finally:
        connection.close()


def database_values(path: Path) -> list[str]:
    connection = sqlite3.connect(path)
    try:
        return [row[0] for row in connection.execute("SELECT value FROM values_table ORDER BY rowid")]
    finally:
        connection.close()


class LeaseTests(unittest.TestCase):
    def test_live_owner_blocks_second_writer(self) -> None:
        with tempfile.TemporaryDirectory() as root:
            lease_path = Path(root) / "profile.lease"
            first = storage.ProfileLease(lease_path, "test")
            first.acquire()
            try:
                with self.assertRaisesRegex(RuntimeError, "already owned"):
                    storage.ProfileLease(lease_path, "test").acquire()
            finally:
                first.release()

    def test_dead_local_owner_requires_explicit_recovery(self) -> None:
        with tempfile.TemporaryDirectory() as root:
            lease_path = Path(root) / "profile.lease"
            lease_path.mkdir()
            (lease_path / "owner.json").write_text(
                json.dumps(
                    {
                        "hostname": storage.socket.gethostname(),
                        "boot_id": storage.boot_id(),
                        "pid": 999999999,
                        "process_start": "missing",
                    }
                ),
                encoding="utf-8",
            )
            lease = storage.ProfileLease(lease_path, "test")
            with self.assertRaisesRegex(RuntimeError, "never reclaimed automatically"):
                lease.acquire()
            recovery = type("Recovery", (), {"lease_dir": str(lease_path), "force": True})()
            self.assertEqual(storage.recover(recovery), 0)
            lease.acquire()
            lease.release()


class CheckpointTests(unittest.TestCase):
    def make_store(self, root: Path, kind: str, local_name: str = "local") -> storage.CheckpointStore:
        return storage.CheckpointStore(
            kind,
            root / local_name,
            root / "config",
            root / "data",
            root / "state",
        )

    def test_opencode_falls_back_from_corrupt_current_generation(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            store = self.make_store(root, "opencode")
            store.restore()
            create_database(store.opencode_db, "first")
            store.checkpoint()
            create_database(store.opencode_db, "second")
            store.checkpoint()

            current = store.current.read_text(encoding="ascii").strip()
            (store.generations / current / "opencode.db").write_bytes(b"not sqlite")

            restored = self.make_store(root, "opencode", "restored")
            restored.restore()
            self.assertEqual(database_values(restored.opencode_db), ["first"])

    def test_opencode_falls_back_from_incomplete_current_generation(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            store = self.make_store(root, "opencode")
            store.restore()
            create_database(store.opencode_db, "first")
            store.checkpoint()
            create_database(store.opencode_db, "second")
            store.checkpoint()

            current = store.current.read_text(encoding="ascii").strip()
            (store.generations / current / "opencode.db").unlink()

            restored = self.make_store(root, "opencode", "restored")
            restored.restore()
            self.assertEqual(database_values(restored.opencode_db), ["first"])

    def test_opencode_v2_does_not_import_or_replace_v1_checkpoints(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            legacy = root / "data/.cscs-agent-storage/opencode"
            generation = legacy / "generations/v1"
            create_database(generation / "opencode.db", "v1-only")
            storage.atomic_json(
                generation / "manifest.json",
                {"version": 2, "kind": "opencode", "files": storage.file_inventory(generation)},
            )
            (legacy / "current").write_text("v1\n")

            store = self.make_store(root, "opencode")
            store.restore()
            self.assertFalse(store.opencode_db.exists())
            create_database(store.opencode_db, "v2-only")
            store.checkpoint()
            restored = self.make_store(root, "opencode", "restored")
            restored.restore()
            self.assertEqual(database_values(restored.opencode_db), ["v2-only"])
            self.assertEqual(database_values(generation / "opencode.db"), ["v1-only"])
            self.assertEqual((legacy / "current").read_text(), "v1\n")

    def test_opencode_restarts_with_fresh_runtime_and_retains_preferences(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            store = self.make_store(root, "opencode")
            store.restore()
            runtime = store.local_root / "opencode-runtime/locks/stale-owner"
            runtime.mkdir(parents=True)
            (runtime / "owner").write_text("dead process")
            preferences = root / "state/opencode/latest/tui/highlights.json"
            preferences.parent.mkdir(parents=True)
            preferences.write_text('{"theme":"user-choice"}\n')
            create_database(store.opencode_db, "saved")
            store.checkpoint()

            store.restore()
            self.assertFalse(runtime.exists())
            self.assertEqual(database_values(store.opencode_db), ["saved"])
            self.assertEqual(json.loads(preferences.read_text()), {"theme": "user-choice"})

    def test_omp_keeps_bulk_data_live_and_checkpoints_sqlite_state(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            persistent_sessions = root / "data" / "omp" / "sessions"
            persistent_sessions.mkdir(parents=True)
            (persistent_sessions / "session.jsonl").write_text("{}\n", encoding="utf-8")
            create_database(root / "data" / "omp" / "agent.db", "legacy")

            store = self.make_store(root, "omp")
            store.restore()
            self.assertTrue((store.omp_data / "sessions").is_symlink())
            self.assertEqual(database_values(store.omp_data / "agent.db"), ["legacy"])

            create_database(store.omp_state / "autoresearch" / "project.db", "state")
            (store.omp_cache / "discard-me").write_text("cache", encoding="utf-8")
            store.checkpoint()

            restored = self.make_store(root, "omp", "restored")
            restored.restore()
            self.assertTrue((restored.omp_data / "sessions").is_symlink())
            self.assertEqual(
                (restored.omp_data / "sessions" / "session.jsonl").read_text(encoding="utf-8"),
                "{}\n",
            )
            self.assertEqual(database_values(restored.omp_data / "agent.db"), ["legacy"])
            self.assertEqual(
                database_values(restored.omp_state / "autoresearch" / "project.db"),
                ["state"],
            )
            self.assertFalse((restored.omp_cache / "discard-me").exists())

    def test_legacy_sqlite_is_staged_before_opening(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            legacy = root / "data" / "omp" / "agent.db"
            legacy.parent.mkdir(parents=True)
            connection = sqlite3.connect(legacy)
            connection.execute("PRAGMA journal_mode=WAL")
            connection.execute("PRAGMA wal_autocheckpoint=0")
            connection.execute("CREATE TABLE values_table (value TEXT NOT NULL)")
            connection.execute("INSERT INTO values_table VALUES ('legacy-wal')")
            connection.commit()
            self.assertTrue(Path(f"{legacy}-wal").is_file())

            real_connect = sqlite3.connect

            def reject_persistent_database(database, *args, **kwargs):
                value = os.fspath(database)
                if value.startswith("file:"):
                    value = value[5:].split("?", 1)[0]
                self.assertNotEqual(Path(value), legacy)
                return real_connect(database, *args, **kwargs)

            try:
                with mock.patch.object(
                    storage.sqlite3, "connect", side_effect=reject_persistent_database
                ):
                    store = self.make_store(root, "omp")
                    store.restore()
            finally:
                connection.close()

            self.assertEqual(database_values(store.omp_data / "agent.db"), ["legacy-wal"])

    def test_checkpoint_never_opens_persistent_sqlite_target(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            store = self.make_store(root, "opencode")
            store.restore()
            create_database(store.opencode_db, "local")
            persistent_data = root / "data"
            real_connect = sqlite3.connect

            def reject_persistent_database(database, *args, **kwargs):
                value = os.fspath(database)
                if value.startswith("file:"):
                    value = value[5:].split("?", 1)[0]
                self.assertFalse(Path(value).is_relative_to(persistent_data))
                return real_connect(database, *args, **kwargs)

            with mock.patch.object(
                storage.sqlite3, "connect", side_effect=reject_persistent_database
            ):
                self.assertTrue(store.checkpoint())

            restored = self.make_store(root, "opencode", "restored-local-publish")
            restored.restore()
            self.assertEqual(database_values(restored.opencode_db), ["local"])

    def test_omp_migrates_all_legacy_bulk_directories(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            legacy_home = root / "config" / "home" / ".omp"
            legacy_agent = legacy_home / "agent"
            agent_directories = ("archive", "blobs", "predict", "sessions")
            root_directories = ("browser-relay", "plugins", "python-env", "remote", "remote-host", "wt")
            for name in agent_directories:
                source = legacy_agent / name
                source.mkdir(parents=True)
                (source / "legacy").write_text(name, encoding="utf-8")
            for name in root_directories:
                source = legacy_home / name
                source.mkdir(parents=True)
                (source / "legacy").write_text(name, encoding="utf-8")

            store = self.make_store(root, "omp")
            store.restore()
            for name in (*agent_directories, *root_directories):
                self.assertTrue((store.omp_data / name).is_symlink())
                self.assertEqual(
                    (store.omp_data / name / "legacy").read_text(encoding="utf-8"),
                    name,
                )

    def test_supervisor_publishes_final_database_and_releases_lease(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            local = root / "local"
            lease = root / "data" / ".cscs-agent-storage" / "opencode.lease"
            result = subprocess.run(
                [
                    sys.executable,
                    storage.__file__,
                    "supervise",
                    "--kind",
                    "opencode",
                    "--lease-dir",
                    str(lease),
                    "--label",
                    "OpenCode test",
                    "--local-root",
                    str(local),
                    "--persistent-config",
                    str(root / "config"),
                    "--persistent-data",
                    str(root / "data"),
                    "--persistent-state",
                    str(root / "state"),
                    "--checkpoint-seconds",
                    "60",
                    "--",
                    sys.executable,
                    "-c",
                    (
                        "import sqlite3,sys; "
                        "db=sqlite3.connect(sys.argv[1]); "
                        "db.execute('create table t(value text)'); "
                        "db.execute(\"insert into t values ('saved')\"); "
                        "db.commit(); db.close()"
                    ),
                    str(local / "opencode.db"),
                ],
                check=False,
            )
            self.assertEqual(result.returncode, 0)
            self.assertFalse(lease.exists())
            restored = self.make_store(root, "opencode", "restored-supervisor")
            restored.restore()
            connection = sqlite3.connect(restored.opencode_db)
            try:
                self.assertEqual(connection.execute("SELECT value FROM t").fetchone()[0], "saved")
            finally:
                connection.close()

    def test_guard_rejects_concurrent_owner(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            lease = Path(directory) / "profile.lease"
            first = subprocess.Popen(
                [
                    sys.executable,
                    storage.__file__,
                    "guard",
                    "--lease-dir",
                    str(lease),
                    "--label",
                    "Prime test",
                    "--",
                    sys.executable,
                    "-c",
                    "import time; time.sleep(30)",
                ]
            )
            try:
                for _ in range(100):
                    if (lease / "owner.json").is_file():
                        break
                    time.sleep(0.02)
                else:
                    self.fail("guard did not acquire its lease")
                second = subprocess.run(
                    [
                        sys.executable,
                        storage.__file__,
                        "guard",
                        "--lease-dir",
                        str(lease),
                        "--label",
                        "Prime test",
                        "--",
                        sys.executable,
                        "-c",
                        "pass",
                    ],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    check=False,
                )
                self.assertEqual(second.returncode, 1)
                self.assertIn("already owned", second.stderr)
            finally:
                first.terminate()
                first.wait(timeout=5)
            self.assertFalse(lease.exists())

    def test_guard_child_dies_with_killed_supervisor(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            lease = root / "profile.lease"
            child_pid_file = root / "child.pid"
            supervisor = subprocess.Popen(
                [
                    sys.executable,
                    storage.__file__,
                    "guard",
                    "--lease-dir",
                    str(lease),
                    "--label",
                    "parent death test",
                    "--",
                    sys.executable,
                    "-c",
                    (
                        "import os,sys,time; "
                        "open(sys.argv[1], 'w').write(str(os.getpid())); "
                        "time.sleep(30)"
                    ),
                    str(child_pid_file),
                ]
            )
            child_pid = None
            try:
                for _ in range(100):
                    if child_pid_file.is_file():
                        child_pid = int(child_pid_file.read_text())
                        break
                    time.sleep(0.02)
                else:
                    self.fail("guard child did not start")

                os.kill(supervisor.pid, signal.SIGKILL)
                supervisor.wait(timeout=5)
                for _ in range(100):
                    status = Path(f"/proc/{child_pid}/status")
                    if not status.exists() or "State:\tZ" in status.read_text():
                        break
                    time.sleep(0.02)
                else:
                    self.fail("guard child survived its supervisor")
            finally:
                if supervisor.poll() is None:
                    supervisor.kill()
                    supervisor.wait(timeout=5)
                if child_pid is not None:
                    try:
                        os.kill(child_pid, signal.SIGKILL)
                    except ProcessLookupError:
                        pass


if __name__ == "__main__":
    unittest.main()
