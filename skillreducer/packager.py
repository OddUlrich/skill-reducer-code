from __future__ import annotations

import zipfile
from pathlib import Path


def package_output(input_dir: Path, archive: Path) -> dict:
    archive.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for path in input_dir.rglob("*"):
            if path.is_file():
                zf.write(path, path.relative_to(input_dir).as_posix())
    return {"archive": str(archive), "input": str(input_dir)}

