#!/usr/bin/env python3
"""Configure Paseo and route its native providers through guarded launchers."""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import uuid
from pathlib import Path

from storage import atomic_json


INSTANCE = re.compile(r"[a-zA-Z0-9][a-zA-Z0-9._-]*\Z")


def private_directory(path: Path) -> Path:
    if path.is_symlink():
        raise RuntimeError(f"profile directory must not be a symlink: {path}")
    path.mkdir(parents=True, exist_ok=True, mode=0o700)
    if path.stat().st_uid != os.getuid():
        raise RuntimeError(f"profile directory is not owned by this user: {path}")
    return path.resolve()


def profile_roots(context: dict, kind: str, instance: str = "default") -> dict[str, str]:
    mode = context["mode"]
    namespace = "opencode-v2" if kind == "opencode" else kind
    if mode == "home":
        return {
            key: str(Path(base) / f"{namespace}-cscs-agents-26.10")
            for key, base in context["host_roots"].items()
        }
    if mode.startswith("project:"):
        base = Path(context["project"]) / ".cscs-agents" / "26.10" / namespace / mode.split(":", 1)[1]
    else:
        base = Path(context["profiles"]) / kind / instance
    return {key: str(base / key) for key in ("config", "data", "cache", "state")}


def prepare(args: argparse.Namespace) -> None:
    mode = args.mode
    if mode not in ("isolated", "home") and not (
        mode.startswith("project:") and INSTANCE.fullmatch(mode.split(":", 1)[1])
    ):
        raise RuntimeError("--harness-profile must be isolated, home, or project:NAME")
    home = private_directory(Path(args.home))
    context = {
        "mode": mode,
        "project": str(Path(args.project).resolve()),
        "home": str(home),
        "profiles": str(private_directory(Path(args.profiles))),
        "launchers": args.launchers,
        "executables": {"omp": args.omp, "opencode": args.opencode},
        "host_roots": dict(zip(("config", "data", "cache", "state"), args.host_roots)),
        "local_storage": args.local_storage,
        "native_options": args.native_option,
    }
    # Native handles must never silently change their owning storage profile.
    selection = Path(args.selection)
    if selection.exists():
        previous = json.loads(selection.read_text())
        if previous != {"mode": mode}:
            raise RuntimeError("harness profile selection differs from this Paseo profile; select a different Paseo instance")
    else:
        atomic_json(selection, {"mode": mode})
    private_directory(Path(args.local_storage))
    private_directory(home / "runtime" / "opencode")
    private_directory((home / "worktrees").resolve())
    roots_by_kind = {kind: profile_roots(context, kind) for kind in ("omp", "opencode")}
    for roots in roots_by_kind.values():
        for root in roots.values():
            path = Path(root)
            if mode.startswith("project:"):
                relative = path.relative_to(context["project"])
                current = Path(context["project"])
                for part in relative.parts:
                    current = private_directory(current / part)
            else:
                private_directory(path)
    if mode.startswith("project:"):
        ignore = Path(context["project"]) / ".cscs-agents" / ".gitignore"
        try:
            with ignore.open("x") as stream:
                stream.write("*\n")
        except FileExistsError:
            pass
    sessions = (
        Path(context["profiles"]) / "omp-sessions"
        if mode == "isolated" else Path(roots_by_kind["omp"]["data"]) / "omp" / "sessions"
    )
    private_directory(sessions)
    context["sessions"] = str(sessions)
    atomic_json(Path(args.context), context)
    command = [sys.executable, str(Path(__file__).resolve()), "provider"]
    managed = {
        "opencode": {"enabled": True, "command": [*command, "opencode", "--"]},
        "omp": {
            "enabled": True,
            "command": [*command, "omp", "--"],
            "options": {"sessionDir": str(sessions)},
        },
    }
    config_path = home / "config.json"
    config = json.loads(config_path.read_text()) if config_path.exists() else {}
    providers = config.setdefault("agents", {}).setdefault("providers", {})
    # These two commands are launcher-owned; preserve other user configuration.
    # Refresh absolute image paths after an image rebuild or architecture change.
    for kind, value in managed.items():
        entry = providers.setdefault(kind, {})
        entry.setdefault("enabled", True)
        entry["command"] = value["command"]
        if "options" in value:
            entry.setdefault("options", {}).update(value["options"])
    for kind in ("claude", "codex", "copilot", "pi"):
        providers.setdefault(kind, {"enabled": False})
    config.setdefault("daemon", {}).setdefault("relay", {})["enabled"] = False
    config.setdefault("worktrees", {})["root"] = str((home / "worktrees").resolve())
    atomic_json(config_path, config)
    # The shell consumes these paths as NUL-delimited mount arguments, not code.
    for roots in roots_by_kind.values():
        for root in roots.values():
            sys.stdout.buffer.write(os.fsencode(root) + b"\0")

def session_argument(arguments: list[str]) -> str | None:
    for index, argument in enumerate(arguments):
        if argument == "--session":
            if index + 1 == len(arguments):
                raise RuntimeError("--session requires a native session path")
            return arguments[index + 1]
        if argument.startswith("--session="):
            return argument.split("=", 1)[1]
    return None


def provider(context: dict, kind: str, arguments: list[str]) -> None:
    if arguments[:1] == ["--"]:
        arguments = arguments[1:]
    # Paseo's OpenCode v2 probe has a five-second deadline. Version checks do
    # not access mutable profiles and must not bootstrap Python or take a lease.
    if arguments in (["--version"], ["-v"]):
        os.execv(context["executables"][kind], [context["executables"][kind], *arguments])
    project = Path(context["project"])
    instance = "default"
    session_dir = Path(context["sessions"]) if kind == "omp" else None
    if kind == "omp" and context["mode"] == "isolated":
        session = session_argument(arguments)
        if session:
            path = Path(session).resolve()
            try:
                instance = path.relative_to(context["sessions"]).parts[0]
            except (ValueError, IndexError):
                raise RuntimeError("OMP session does not belong to this Paseo profile") from None
            if not re.fullmatch(r"[0-9a-f]{32}", instance) or not path.is_file():
                raise RuntimeError("OMP session does not identify an existing isolated profile")
        else:
            instance = uuid.uuid4().hex
        session_dir = private_directory(Path(context["sessions"]) / instance)
    roots = profile_roots(context, kind, instance)
    for root in roots.values():
        private_directory(Path(root))
    command = [str(Path(context["launchers"]) / f"{kind}-bwrap"), "--project-dir", str(project)]
    for key, root in roots.items():
        command.extend([f"--{key}-dir", root])
    if kind == "opencode":
        plugins = str(Path(context["home"]) / "runtime" / "opencode")
        command.extend(["--ro-bind", f"{plugins}:{plugins}"])
    else:
        cwd = Path.cwd().resolve()
        worktrees = (Path(context["home"]) / "worktrees").resolve()
        if not cwd.is_relative_to(project) and not cwd.is_relative_to(worktrees):
            raise RuntimeError("OMP working directory is outside the exposed project/worktrees")
        # OMP launches in each workspace; OpenCode's helper instead has one
        # neutral server cwd and receives actual workspace paths over HTTP.
        command[2] = str(cwd)
        if session_dir:
            os.environ["PI_CODING_AGENT_SESSION_DIR"] = str(session_dir)
            command.extend(["--bind", f"{session_dir}:{session_dir}"])
    worktrees = str((Path(context["home"]) / "worktrees").resolve())
    command.extend([*context["native_options"], "--bind", f"{worktrees}:{worktrees}", "--", *arguments])
    os.environ["CSCS_AGENT_LOCAL_STORAGE_DIR"] = context["local_storage"]
    os.execv(command[0], command)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="action", required=True)
    setup = subparsers.add_parser("prepare")
    for option in ("home", "profiles", "project", "launchers", "omp", "opencode", "local-storage", "context", "selection"):
        setup.add_argument(f"--{option}", required=True)
    setup.add_argument("--mode", default="isolated")
    setup.add_argument("--host-roots", nargs=4, required=True)
    setup.add_argument("--native-option", action="append", default=[])
    native = subparsers.add_parser("provider")
    native.add_argument("kind", choices=("omp", "opencode"))
    native.add_argument("arguments", nargs=argparse.REMAINDER)
    args = parser.parse_args()
    try:
        if args.action == "prepare":
            prepare(args)
        else:
            context = json.loads(Path(os.environ["CSCS_PASEO_CONTEXT"]).read_text())
            provider(context, args.kind, args.arguments)
        return 0
    except (OSError, ValueError, RuntimeError, KeyError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
