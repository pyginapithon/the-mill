"""List agent_coord modules that nothing imports.

Usage:
  python tools/orphan_scan.py
  python tools/orphan_scan.py --root path/to/the-mill

Seeds are the console scripts in pyproject.toml, every tests/ import, and
`python -m agent_coord...` strings. Importing a package runs its __init__,
so that file's imports count. `from . import name` counts as the submodule.
A file loaded by path (importlib spec_from_file_location) counts too.

Exit 0. Prints one orphan per line: module, then repo-relative path.
wall_ui_save is a snapshot tree and is not scanned.
"""

from __future__ import annotations

import ast
import re
import sys
import tomllib
from pathlib import Path

SKIP_PARTS = frozenset({"__pycache__", "wall_ui_save"})
_PY_M = re.compile(r"python -m (agent_coord(?:\.[\w]+)*)")


def _repo_root(argv: list[str]) -> Path:
    if "--root" in argv:
        i = argv.index("--root")
        return Path(argv[i + 1]).resolve()
    return Path(__file__).resolve().parents[1]


def _module_name(path: Path, pkg: Path) -> tuple[str, bool]:
    rel = path.relative_to(pkg).with_suffix("")
    parts = list(rel.parts)
    is_pkg = parts[-1] == "__init__"
    if is_pkg:
        parts = parts[:-1]
    name = "agent_coord" + (("." + ".".join(parts)) if parts else "")
    return name, is_pkg


def _known_child(module: str, name: str, known: set[str]) -> str | None:
    """`from package import member` loads member.py when that module exists."""
    if name == "*":
        return None
    child = f"{module}.{name}" if module else name
    return child if child in known else None


def _imports(path: Path, module: str, is_pkg: bool, known: set[str]) -> set[str]:
    """agent_coord modules this file imports."""
    base = module.split(".")
    rel_base = base if is_pkg else base[:-1]
    out: set[str] = set()
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"))
    except SyntaxError:
        return out
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name == "agent_coord" or alias.name.startswith("agent_coord."):
                    out.add(alias.name)
        elif isinstance(node, ast.ImportFrom):
            if node.level:
                parent = rel_base[:]
                up = node.level - 1
                if up:
                    parent = parent[:-up] if up <= len(parent) else []
                if node.module:
                    mod = ".".join(parent + [node.module])
                    out.add(mod)
                    for alias in node.names or []:
                        child = _known_child(mod, alias.name, known)
                        if child:
                            out.add(child)
                else:
                    for alias in node.names or []:
                        if alias.name != "*":
                            out.add(".".join(parent + [alias.name]))
            elif node.module and (
                node.module == "agent_coord" or node.module.startswith("agent_coord.")
            ):
                out.add(node.module)
                for alias in node.names or []:
                    child = _known_child(node.module, alias.name, known)
                    if child:
                        out.add(child)
    return out


def _file_loads(path: Path, pkg: Path) -> set[str]:
    """Modules loaded by a path next to this file, not by import."""
    text = path.read_text(encoding="utf-8")
    if "spec_from_file_location" not in text and "exec_module" not in text:
        return set()
    found: set[str] = set()
    for match in re.finditer(r"""["']([^"']+\.py)["']""", text):
        name = Path(match.group(1))
        candidates = [
            (path.parent / name).resolve(),
            (path.parent / "lib" / name.name).resolve(),
        ]
        for candidate in candidates:
            try:
                candidate.relative_to(pkg)
            except ValueError:
                continue
            if candidate.is_file():
                mod, _ = _module_name(candidate, pkg)
                found.add(mod)
    return found


def _seeds(root: Path, test_imports: set[str]) -> set[str]:
    seeds = set(test_imports)
    pyproject = root / "pyproject.toml"
    if pyproject.is_file():
        data = tomllib.loads(pyproject.read_text(encoding="utf-8"))
        for target in (data.get("project") or {}).get("scripts") or {}:
            mod = str(target).split(":", 1)[0]
            if mod == "agent_coord" or mod.startswith("agent_coord."):
                seeds.add(mod)
    for folder in (root / "agent_coord", root / "tests", root / "scripts"):
        if not folder.is_dir():
            continue
        for path in folder.rglob("*.py"):
            if any(part in SKIP_PARTS for part in path.parts):
                continue
            text = path.read_text(encoding="utf-8", errors="ignore")
            for match in _PY_M.finditer(text):
                seeds.add(match.group(1))
    return seeds


def scan(root: Path) -> list[tuple[str, Path]]:
    pkg = root / "agent_coord"
    modules: dict[str, Path] = {}
    is_pkg: dict[str, bool] = {}
    edges: dict[str, set[str]] = {}
    for path in pkg.rglob("*.py"):
        if any(part in SKIP_PARTS for part in path.parts):
            continue
        name, pkg_init = _module_name(path, pkg)
        modules[name] = path
        is_pkg[name] = pkg_init
    known = set(modules)
    for name, path in list(modules.items()):
        edges[name] = _imports(path, name, is_pkg[name], known) | _file_loads(path, pkg)

    test_imports: set[str] = set()
    tests = root / "tests"
    if tests.is_dir():
        for path in tests.rglob("*.py"):
            if "__pycache__" in path.parts:
                continue
            test_imports |= _imports(path, "tests.scan", False, known)

    seen: set[str] = set()
    stack = [s for s in _seeds(root, test_imports) if s == "agent_coord" or s.startswith("agent_coord.")]
    while stack:
        current = stack.pop()
        if current in seen:
            continue
        seen.add(current)
        for dep in edges.get(current, ()):
            if dep not in seen:
                stack.append(dep)
        # Importing agent_coord.a.b runs each parent package's __init__.py.
        parts = current.split(".")
        for i in range(1, len(parts)):
            parent = ".".join(parts[:i])
            if parent not in seen:
                stack.append(parent)
    orphans = []
    for name, path in sorted(modules.items()):
        if name not in seen:
            orphans.append((name, path.relative_to(root)))
    return orphans


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    root = _repo_root(args)
    orphans = scan(root)
    for name, rel in orphans:
        print(f"{name}\t{rel.as_posix()}")
    print(f"# {len(orphans)} orphan module(s)", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
