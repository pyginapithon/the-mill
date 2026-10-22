# CI install locks (#634)

Every package CI installs from PyPI comes from one of these files, installed
with `pip install --require-hashes`, so a compromised CA, mirror or index
cannot swap a package into a run that release.yml gates on.

- `build.txt` - the build env for `python -m build --no-isolation` (build_pack).
- `ci.txt` - runtime deps of the pack, test tools, twine, pip-audit, setuptools.
- `desk.txt` - the released desk client for copilot-setup-steps.yml (`--no-deps`).

The local `dist/` files install with `--no-deps --no-build-isolation`, then
`pip check` proves ci.txt satisfies the pack's own requirements.

Regenerate after editing a `.in` file (the command is in each `.txt` header):

    uv pip compile --generate-hashes --python-version 3.12 --python-platform x86_64-manylinux_2_28 tools/ci-lock/ci.in -o tools/ci-lock/ci.txt

`ci.in` starts with the `[project] dependencies` lines of pyproject.toml,
verbatim; tests/install/test_github_workflows.py fails when they drift.
Dependabot refreshes the pins weekly.
