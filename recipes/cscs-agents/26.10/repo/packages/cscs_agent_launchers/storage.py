#!/usr/bin/env python3
"""Single-writer profile leases and node-local state checkpoints."""

from __future__ import annotations

import argparse
import ctypes
import hashlib
import json
import os
import shutil
import signal
import socket
import sqlite3
import subprocess
import sys
import tempfile
import time
import uuid
from collections.abc import Callable
from pathlib import Path


ACTIVE_SLURM_STATES = {
    "CONFIGURING",
    "COMPLETING",
    "PENDING",
    "RESIZING",
    "RUNNING",
    "STAGE_OUT",
    "SUSPENDED",
}
TERMINAL_SLURM_STATES = {
    "BOOT_FAIL",
    "CANCELLED",
    "COMPLETED",
    "DEADLINE",
    "FAILED",
    "NODE_FAIL",
    "OUT_OF_MEMORY",
    "PREEMPTED",
    "REVOKED",
    "TIMEOUT",
}
OMP_PERSISTENT_DATA_DIRS = (
    "archive",
    "blobs",
    "browser-relay",
    "plugins",
    "predict",
    "python-env",
    "remote",
    "remote-host",
    "sessions",
    "wt",
)
OMP_VOLATILE_STATE_DIRS = {"browser-profiles", "run", "ssh-control"}
SQLITE_SIDECARS = ("-journal", "-shm", "-wal")


def warn(message: str) -> None:
    print(f"warning: {message}", file=sys.stderr, flush=True)


def fsync_path(path: Path) -> None:
    flags = os.O_RDONLY
    if path.is_dir():
        flags |= getattr(os, "O_DIRECTORY", 0)
    fd = os.open(path, flags)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def atomic_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{os.getpid()}.{uuid.uuid4().hex}.tmp")
    with temporary.open("w", encoding="utf-8") as stream:
        json.dump(value, stream, sort_keys=True)
        stream.write("\n")
        stream.flush()
        os.fsync(stream.fileno())
    os.chmod(temporary, 0o600)
    os.replace(temporary, path)
    fsync_path(path.parent)


def atomic_text(path: Path, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{os.getpid()}.{uuid.uuid4().hex}.tmp")
    with temporary.open("w", encoding="utf-8") as stream:
        stream.write(value)
        stream.flush()
        os.fsync(stream.fileno())
    os.chmod(temporary, 0o600)
    os.replace(temporary, path)
    fsync_path(path.parent)


def boot_id() -> str:
    try:
        return Path("/proc/sys/kernel/random/boot_id").read_text(encoding="ascii").strip()
    except OSError:
        return "unknown"


def process_start(pid: int) -> str | None:
    try:
        fields = Path(f"/proc/{pid}/stat").read_text(encoding="ascii").split()
    except (OSError, ValueError):
        return None
    return fields[21] if len(fields) > 21 else None


def slurm_job_active(job_id: str) -> bool | None:
    scontrol = shutil.which("scontrol")
    if not scontrol:
        return None
    try:
        result = subprocess.run(
            [scontrol, "show", "job", "-h", "-o", job_id],
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True,
            timeout=10,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    if result.returncode != 0 or not result.stdout.strip():
        return None
    for field in result.stdout.split():
        if field.startswith("JobState="):
            state = field.split("=", 1)[1].split("+", 1)[0]
            if state in ACTIVE_SLURM_STATES:
                return True
            if state in TERMINAL_SLURM_STATES:
                return False
            return None
    return None


class ProfileLease:
    def __init__(self, path: Path, label: str, *, serialized: bool = True):
        self.path = path
        self.recovery_path = path.with_name(f"{path.name}.recovery")
        self.operation_path = path.with_name(f"{path.name}.operation")
        self.label = label
        self.serialized = serialized
        self.token = uuid.uuid4().hex
        self.metadata_path = path / "owner.json"
        self.heartbeat_path = path / f"heartbeat.{self.token}"
        self.metadata = {
            "version": 1,
            "label": label,
            "token": self.token,
            "hostname": socket.gethostname(),
            "boot_id": boot_id(),
            "pid": os.getpid(),
            "process_start": process_start(os.getpid()),
            "slurm_job_id": os.environ.get("SLURM_JOB_ID"),
            "slurm_step_id": os.environ.get("SLURM_STEP_ID"),
            "created": int(time.time()),
        }

    def _read_owner(self) -> dict[str, object]:
        try:
            value = json.loads(self.metadata_path.read_text(encoding="utf-8"))
            return value if isinstance(value, dict) else {}
        except (OSError, ValueError):
            return {}

    def _owner_state(self, owner: dict[str, object]) -> str:
        hostname = owner.get("hostname")
        owner_boot = owner.get("boot_id")
        owner_pid = owner.get("pid")
        if hostname == socket.gethostname() and owner_boot == boot_id():
            try:
                pid = int(owner_pid)
            except (TypeError, ValueError):
                return "stale"
            actual_start = process_start(pid)
            if actual_start is None:
                return "stale"
            expected_start = owner.get("process_start")
            return "active" if expected_start in (None, actual_start) else "stale"

        job_id = owner.get("slurm_job_id")
        if isinstance(job_id, str) and job_id:
            active = slurm_job_active(job_id)
            if active is True:
                return "active"
            if active is False:
                return "stale"
        return "unknown"

    def _quarantine(self, reason: str) -> Path:
        quarantine = self.path.with_name(
            f"{self.path.name}.{reason}.{int(time.time())}.{uuid.uuid4().hex}"
        )
        os.rename(self.path, quarantine)
        fsync_path(self.path.parent)
        return quarantine

    def _acquire(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if self.recovery_path.exists():
            raise RuntimeError(f"{self.label} profile recovery is in progress: {self.recovery_path}")
        try:
            self.path.mkdir(mode=0o700)
        except FileExistsError:
            owner = self._read_owner()
            state = self._owner_state(owner)
            detail = json.dumps(owner, sort_keys=True) if owner else "unreadable owner metadata"
            raise RuntimeError(
                f"{self.label} profile is already owned ({state}): {detail}. "
                "Stale leases are never reclaimed automatically; use --recover-storage "
                "only after verifying that the recorded owner is gone."
            )
        atomic_json(self.metadata_path, self.metadata)
        self.heartbeat()
        if self.recovery_path.exists():
            self._release()
            raise RuntimeError(f"{self.label} profile recovery started during lease acquisition")

    def acquire(self) -> None:
        if not self.serialized:
            self._acquire()
            return
        operation = ProfileLease(
            self.operation_path, f"{self.label} lease operation", serialized=False
        )
        operation.acquire()
        try:
            self._acquire()
        finally:
            operation.release()

    def heartbeat(self) -> None:
        atomic_text(self.heartbeat_path, f"{int(time.time())} {self.token}\n")

    def _release(self) -> None:
        owner = self._read_owner()
        if owner.get("token") != self.token:
            warn(f"refusing to release a {self.label} lease owned by another process")
            return
        try:
            quarantine = self._quarantine("released")
        except FileNotFoundError:
            return
        shutil.rmtree(quarantine, ignore_errors=True)

    def release(self) -> None:
        if not self.serialized:
            self._release()
            return
        operation = ProfileLease(
            self.operation_path, f"{self.label} lease operation", serialized=False
        )
        operation.acquire()
        try:
            self._release()
        finally:
            operation.release()


def remove_sqlite(path: Path) -> None:
    for candidate in (path, *(Path(f"{path}{suffix}") for suffix in SQLITE_SIDECARS)):
        try:
            candidate.unlink()
        except FileNotFoundError:
            pass


def sqlite_backup(source: Path, target: Path, *, source_mode: str = "ro") -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = target.with_name(f".{target.name}.{os.getpid()}.{uuid.uuid4().hex}.tmp")
    remove_sqlite(temporary)
    source_db = sqlite3.connect(f"file:{source}?mode={source_mode}", uri=True, timeout=30)
    target_db = sqlite3.connect(temporary, timeout=30)
    try:
        source_db.backup(target_db)
        result = target_db.execute("PRAGMA quick_check").fetchone()
        if not result or result[0] != "ok":
            raise RuntimeError(f"SQLite quick_check failed for {source}: {result}")
        target_db.execute("PRAGMA journal_mode=DELETE")
    finally:
        target_db.close()
        source_db.close()
    os.chmod(temporary, 0o600)
    fsync_path(temporary)
    os.replace(temporary, target)
    fsync_path(target.parent)


def sqlite_file_signature(path: Path) -> tuple[tuple[str, int, int] | None, ...]:
    result = []
    for candidate in (path, *(Path(f"{path}{suffix}") for suffix in SQLITE_SIDECARS)):
        try:
            metadata = candidate.stat()
        except FileNotFoundError:
            result.append(None)
        else:
            result.append((candidate.name, metadata.st_size, metadata.st_mtime_ns))
    return tuple(result)


def import_sqlite(source: Path, target: Path) -> None:
    """Stage an NFS database locally before asking SQLite to read it."""

    target.parent.mkdir(parents=True, exist_ok=True)
    for _ in range(3):
        before = sqlite_file_signature(source)
        with tempfile.TemporaryDirectory(prefix=f".{target.name}.import.", dir=target.parent) as root:
            staged = Path(root) / source.name
            copy_regular_stable(source, staged)
            for suffix in ("-journal", "-wal"):
                sidecar = Path(f"{source}{suffix}")
                if sidecar.is_file():
                    copy_regular_stable(sidecar, Path(f"{staged}{suffix}"))
            if sqlite_file_signature(source) != before:
                continue
            sqlite_backup(staged, target, source_mode="rw")
            return
    raise RuntimeError(f"database changed continuously while importing: {source}")


def export_sqlite(source: Path, target: Path, scratch: Path) -> None:
    """Finalize a local SQLite snapshot before publishing it to NFS."""

    scratch.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=".sqlite-export.", dir=scratch) as root:
        snapshot = Path(root) / source.name
        sqlite_backup(source, snapshot)
        copy_regular_stable(snapshot, target)


def copy_regular_stable(source: Path, target: Path) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    for _ in range(3):
        before = source.stat()
        temporary = target.with_name(f".{target.name}.{os.getpid()}.{uuid.uuid4().hex}.tmp")
        shutil.copy2(source, temporary)
        after = source.stat()
        if (before.st_size, before.st_mtime_ns) == (after.st_size, after.st_mtime_ns):
            fsync_path(temporary)
            os.replace(temporary, target)
            return
        temporary.unlink(missing_ok=True)
    raise RuntimeError(f"file changed continuously while checkpointing: {source}")


def copy_tree(
    source: Path,
    target: Path,
    *,
    sqlite_safe: bool,
    excluded_top: set[str] | None = None,
    sqlite_copy: Callable[[Path, Path], None] = sqlite_backup,
) -> None:
    excluded_top = excluded_top or set()
    target.mkdir(parents=True, exist_ok=True)
    if not source.is_dir():
        return
    for root, directories, files in os.walk(source, followlinks=False):
        root_path = Path(root)
        relative = root_path.relative_to(source)
        if relative.parts and relative.parts[0] in excluded_top:
            directories[:] = []
            continue
        directories[:] = [
            name
            for name in directories
            if not (root_path / name).is_symlink()
            and not (relative == Path(".") and name in excluded_top)
        ]
        destination_root = target / relative
        destination_root.mkdir(parents=True, exist_ok=True)
        try:
            shutil.copystat(root_path, destination_root, follow_symlinks=False)
        except OSError:
            pass
        for name in files:
            item = root_path / name
            if item.is_symlink() or any(name.endswith(suffix) for suffix in SQLITE_SIDECARS):
                continue
            destination = destination_root / name
            if sqlite_safe and name.endswith(".db"):
                sqlite_copy(item, destination)
            else:
                copy_regular_stable(item, destination)


def validate_tree(root: Path) -> None:
    for database in root.rglob("*.db"):
        connection = sqlite3.connect(f"file:{database}?mode=ro", uri=True, timeout=10)
        try:
            result = connection.execute("PRAGMA quick_check").fetchone()
        finally:
            connection.close()
        if not result or result[0] != "ok":
            raise RuntimeError(f"invalid SQLite checkpoint {database}: {result}")


def file_inventory(root: Path) -> list[dict[str, object]]:
    inventory = []
    for path in sorted(root.rglob("*")):
        if not path.is_file() or path.name == "manifest.json":
            continue
        digest = hashlib.sha256()
        with path.open("rb") as stream:
            for block in iter(lambda: stream.read(1024 * 1024), b""):
                digest.update(block)
        inventory.append(
            {
                "path": str(path.relative_to(root)),
                "size": path.stat().st_size,
                "sha256": digest.hexdigest(),
            }
        )
    return inventory


def validate_inventory(root: Path, inventory: object) -> None:
    if not isinstance(inventory, list):
        raise RuntimeError(f"checkpoint has no file inventory: {root}")
    actual = file_inventory(root)
    if actual != inventory:
        raise RuntimeError(f"checkpoint file inventory mismatch: {root}")


class CheckpointStore:
    def __init__(
        self,
        kind: str,
        local_root: Path,
        persistent_config: Path,
        persistent_data: Path,
        persistent_state: Path,
    ):
        self.kind = kind
        self.local_root = local_root
        self.persistent_config = persistent_config
        self.persistent_data = persistent_data
        self.persistent_state = persistent_state
        self.store = persistent_data / ".cscs-agent-storage" / kind
        self.generations = self.store / "generations"
        self.current = self.store / "current"

    @property
    def opencode_db(self) -> Path:
        return self.local_root / "opencode.db"

    @property
    def omp_data(self) -> Path:
        return self.local_root / "data" / "omp"

    @property
    def omp_state(self) -> Path:
        return self.local_root / "state" / "omp"

    @property
    def omp_cache(self) -> Path:
        return self.local_root / "cache" / "omp"

    def _reset_local(self) -> None:
        self.local_root.mkdir(parents=True, exist_ok=True)
        os.chmod(self.local_root, 0o700)
        if self.kind == "opencode":
            remove_sqlite(self.opencode_db)
            return
        for name in ("data", "state", "cache"):
            shutil.rmtree(self.local_root / name, ignore_errors=True)
        self.omp_data.mkdir(parents=True, exist_ok=True)
        self.omp_state.mkdir(parents=True, exist_ok=True)
        self.omp_cache.mkdir(parents=True, exist_ok=True)

    def _generation_candidates(self) -> list[Path]:
        candidates: list[Path] = []
        try:
            current_name = self.current.read_text(encoding="ascii").strip()
        except OSError:
            current_name = ""
        if current_name:
            candidates.append(self.generations / current_name)
        if self.generations.is_dir():
            for candidate in sorted(self.generations.iterdir(), reverse=True):
                if candidate.is_dir() and candidate not in candidates and not candidate.name.startswith("."):
                    candidates.append(candidate)
        return candidates

    def _restore_generation(self, generation: Path) -> None:
        manifest = json.loads((generation / "manifest.json").read_text(encoding="utf-8"))
        if manifest.get("version") != 2 or manifest.get("kind") != self.kind:
            raise RuntimeError(f"incompatible checkpoint manifest in {generation}")
        validate_inventory(generation, manifest.get("files"))
        if self.kind == "opencode":
            source = generation / "opencode.db"
            if source.is_file():
                copy_regular_stable(source, self.opencode_db)
                validate_tree(self.local_root)
            return
        copy_tree(generation / "data", self.omp_data, sqlite_safe=False)
        copy_tree(generation / "state", self.omp_state, sqlite_safe=False)
        validate_tree(self.local_root)

    def _legacy_opencode(self) -> None:
        app_data = self.persistent_data / "opencode"
        for name in ("opencode-local.db", "opencode.db", "opencode-stable.db"):
            candidate = app_data / name
            if candidate.is_file():
                import_sqlite(candidate, self.opencode_db)
                warn(f"imported legacy OpenCode database from {candidate}")
                return

    def _legacy_omp(self) -> None:
        persistent_data = self.persistent_data / "omp"
        persistent_state = self.persistent_state / "omp"
        copy_tree(
            persistent_data,
            self.omp_data,
            sqlite_safe=True,
            excluded_top=set(OMP_PERSISTENT_DATA_DIRS),
            sqlite_copy=import_sqlite,
        )
        copy_tree(
            persistent_state,
            self.omp_state,
            sqlite_safe=True,
            excluded_top=OMP_VOLATILE_STATE_DIRS,
            sqlite_copy=import_sqlite,
        )

        legacy_home = self.persistent_config / "home" / ".omp"
        legacy_agent = legacy_home / "agent"
        for name in ("agent.db", "history.db", "models.db", "skill-descriptions.db"):
            target = self.omp_data / name
            source = legacy_agent / name
            if not target.exists() and source.is_file():
                import_sqlite(source, target)
                warn(f"imported legacy OMP database from {source}")
        for name in ("autoqa.db", "stats.db"):
            target = self.omp_data / name
            source = legacy_home / name
            if not target.exists() and source.is_file():
                import_sqlite(source, target)
                warn(f"imported legacy OMP database from {source}")
        for name in ("archive", "blobs", "predict", "sessions"):
            source = legacy_agent / name
            target = persistent_data / name
            if source.is_dir() and not target.exists():
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copytree(source, target, symlinks=True)
                warn(f"migrated legacy OMP {name} directory from {source}")
        for name in ("browser-relay", "plugins", "python-env", "remote", "remote-host", "wt"):
            source = legacy_home / name
            target = persistent_data / name
            if source.is_dir() and not target.exists():
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copytree(source, target, symlinks=True)
                warn(f"migrated legacy OMP {name} directory from {source}")

    def _prepare_omp_links(self) -> None:
        persistent_data = self.persistent_data / "omp"
        persistent_data.mkdir(parents=True, exist_ok=True)
        for name in OMP_PERSISTENT_DATA_DIRS:
            persistent = persistent_data / name
            local = self.omp_data / name
            persistent.mkdir(parents=True, exist_ok=True)
            if local.is_symlink():
                local.unlink()
            elif local.exists():
                if local.is_dir() and not any(local.iterdir()):
                    local.rmdir()
                else:
                    raise RuntimeError(f"checkpoint conflicts with persistent OMP directory: {local}")
            local.symlink_to(persistent, target_is_directory=True)

    def restore(self) -> None:
        self._reset_local()
        restored = False
        for generation in self._generation_candidates():
            try:
                self._restore_generation(generation)
            except (OSError, ValueError, RuntimeError, sqlite3.DatabaseError) as error:
                warn(f"ignored invalid {self.kind} checkpoint {generation}: {error}")
                self._reset_local()
                continue
            restored = True
            break
        if not restored:
            if self.kind == "opencode":
                self._legacy_opencode()
            else:
                self._legacy_omp()
        if self.kind == "omp":
            self._prepare_omp_links()

    def checkpoint(self) -> bool:
        if self.kind == "opencode" and not self.opencode_db.is_file():
            return False
        self.generations.mkdir(parents=True, exist_ok=True)
        generation_name = f"{time.time_ns()}-{uuid.uuid4().hex[:8]}"
        temporary = self.generations / f".{generation_name}.tmp"
        final = self.generations / generation_name
        temporary.mkdir(mode=0o700)
        try:
            if self.kind == "opencode":
                export_sqlite(
                    self.opencode_db,
                    temporary / "opencode.db",
                    self.local_root,
                )
            else:
                sqlite_export = lambda source, target: export_sqlite(
                    source, target, self.local_root
                )
                copy_tree(
                    self.omp_data,
                    temporary / "data",
                    sqlite_safe=True,
                    sqlite_copy=sqlite_export,
                )
                copy_tree(
                    self.omp_state,
                    temporary / "state",
                    sqlite_safe=True,
                    excluded_top=OMP_VOLATILE_STATE_DIRS,
                    sqlite_copy=sqlite_export,
                )
            atomic_json(
                temporary / "manifest.json",
                {
                    "version": 2,
                    "kind": self.kind,
                    "created": int(time.time()),
                    "files": file_inventory(temporary),
                },
            )
            fsync_path(temporary)
            os.rename(temporary, final)
            fsync_path(self.generations)
            atomic_text(self.current, f"{generation_name}\n")
            self._prune(generation_name)
            return True
        except Exception:
            shutil.rmtree(temporary, ignore_errors=True)
            raise

    def _prune(self, current_name: str) -> None:
        complete = sorted(
            (
                path
                for path in self.generations.iterdir()
                if path.is_dir() and not path.name.startswith(".")
            ),
            reverse=True,
        )
        keep = {path.name for path in complete[:2]}
        keep.add(current_name)
        for path in complete:
            if path.name not in keep:
                shutil.rmtree(path, ignore_errors=True)


def child_status(returncode: int) -> int:
    return 128 - returncode if returncode < 0 else returncode


def parent_death_hook(parent_pid: int):
    """Kill a not-yet-execed child if its Python supervisor disappears."""

    def arm() -> None:
        libc = ctypes.CDLL(None, use_errno=True)
        if libc.prctl(1, signal.SIGKILL, 0, 0, 0) != 0:
            os._exit(127)
        if os.getppid() != parent_pid:
            os.kill(os.getpid(), signal.SIGKILL)

    return arm


def supervise(args: argparse.Namespace, checkpoint: bool) -> int:
    lease = ProfileLease(Path(args.lease_dir), args.label)
    lease.acquire()
    store = None
    try:
        if checkpoint:
            store = CheckpointStore(
                args.kind,
                Path(args.local_root),
                Path(args.persistent_config),
                Path(args.persistent_data),
                Path(args.persistent_state),
            )
            store.restore()
    except Exception:
        lease.release()
        raise

    command = args.command
    if command and command[0] == "--":
        command = command[1:]
    if not command:
        lease.release()
        raise RuntimeError("missing supervised command")

    child: subprocess.Popen[bytes] | None = None
    pending_signal: int | None = None

    def forward(signum: int, _frame: object) -> None:
        nonlocal pending_signal
        if child is not None and child.poll() is None:
            os.killpg(child.pid, signum)
        else:
            pending_signal = signum

    old_handlers = {}
    for signum in (signal.SIGHUP, signal.SIGINT, signal.SIGTERM):
        old_handler = signal.getsignal(signum)
        if old_handler != signal.SIG_IGN:
            old_handlers[signum] = signal.signal(signum, forward)

    final_checkpoint_ok = True
    try:
        child = subprocess.Popen(
            command,
            start_new_session=True,
            preexec_fn=parent_death_hook(os.getpid()),
        )
        if pending_signal is not None:
            os.killpg(child.pid, pending_signal)
        next_heartbeat = time.monotonic() + 10
        next_checkpoint = time.monotonic() + args.checkpoint_seconds
        while child.poll() is None:
            now = time.monotonic()
            if now >= next_heartbeat:
                try:
                    lease.heartbeat()
                except OSError as error:
                    warn(f"could not refresh {args.label} lease heartbeat: {error}")
                next_heartbeat = now + 10
            if store is not None and now >= next_checkpoint:
                try:
                    store.checkpoint()
                except Exception as error:
                    warn(f"periodic {args.kind} checkpoint failed; retaining prior generation: {error}")
                next_checkpoint = now + args.checkpoint_seconds
            time.sleep(0.25)
        status = child_status(child.returncode)
        if store is not None:
            try:
                store.checkpoint()
            except Exception as error:
                final_checkpoint_ok = False
                warn(f"final {args.kind} checkpoint failed: {error}")
        return status if status != 0 or final_checkpoint_ok else 1
    except BaseException:
        if child is not None and child.poll() is None:
            os.killpg(child.pid, signal.SIGTERM)
            try:
                child.wait(timeout=5)
            except subprocess.TimeoutExpired:
                os.killpg(child.pid, signal.SIGKILL)
                child.wait()
        raise
    finally:
        for signum, handler in old_handlers.items():
            signal.signal(signum, handler)
        lease.release()


def recover_path(path: Path, force: bool, label: str) -> int:
    recovery_path = path.with_name(f"{path.name}.recovery")
    try:
        recovery_path.mkdir(mode=0o700)
    except FileExistsError:
        raise RuntimeError(f"another profile recovery is already in progress: {recovery_path}")
    try:
        if not path.exists():
            print(f"no profile lease exists: {path}")
            return 0
        owner_path = path / "owner.json"
        try:
            owner = json.loads(owner_path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            owner = {}
        probe = ProfileLease(path, label, serialized=False)
        state = probe._owner_state(owner)
        if state == "active":
            print(json.dumps(owner, indent=2, sort_keys=True))
            raise RuntimeError("refusing to recover a lease whose recorded owner is active")
        if not force:
            print(json.dumps(owner, indent=2, sort_keys=True))
            raise RuntimeError("refusing recovery without --force")
        quarantine = path.with_name(f"{path.name}.recovered.{int(time.time())}.{uuid.uuid4().hex}")
        os.rename(path, quarantine)
        fsync_path(path.parent)
        print(f"quarantined profile lease as {quarantine}")
        return 0
    finally:
        recovery_path.rmdir()


def recover(args: argparse.Namespace) -> int:
    path = Path(args.lease_dir)
    operation_path = path.with_name(f"{path.name}.operation")
    if operation_path.exists():
        recover_path(operation_path, args.force, "lease operation")
    operation = ProfileLease(operation_path, "lease operation", serialized=False)
    try:
        operation.acquire()
    except RuntimeError:
        # A stale NFS negative lookup may have hidden the operation directory
        # until mkdir reached the server. Recovery remains explicit here.
        recover_path(operation_path, args.force, "lease operation")
        operation = ProfileLease(operation_path, "lease operation", serialized=False)
        operation.acquire()
    try:
        return recover_path(path, args.force, "profile")
    finally:
        operation.release()


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser()
    subparsers = result.add_subparsers(dest="action", required=True)

    for action in ("supervise", "guard"):
        command = subparsers.add_parser(action)
        command.add_argument("--lease-dir", required=True)
        command.add_argument("--label", required=True)
        if action == "supervise":
            command.add_argument("--kind", choices=("opencode", "omp"), required=True)
            command.add_argument("--local-root", required=True)
            command.add_argument("--persistent-config", required=True)
            command.add_argument("--persistent-data", required=True)
            command.add_argument("--persistent-state", required=True)
            command.add_argument("--checkpoint-seconds", type=int, default=30)
        else:
            command.set_defaults(checkpoint_seconds=30)
        command.add_argument("command", nargs=argparse.REMAINDER)

    command = subparsers.add_parser("recover")
    command.add_argument("--lease-dir", required=True)
    command.add_argument("--force", action="store_true")
    return result


def main() -> int:
    args = parser().parse_args()
    try:
        if args.action == "supervise":
            return supervise(args, checkpoint=True)
        if args.action == "guard":
            return supervise(args, checkpoint=False)
        return recover(args)
    except (OSError, RuntimeError, sqlite3.DatabaseError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
