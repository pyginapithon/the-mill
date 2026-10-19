"""Write pack-deps.txt from pyproject.toml project.dependencies."""
import pathlib
import tomllib

data = tomllib.loads(pathlib.Path("pyproject.toml").read_text(encoding="utf-8"))
pathlib.Path("pack-deps.txt").write_text(
    "\n".join(data["project"]["dependencies"]) + "\n",
    encoding="utf-8",
)
