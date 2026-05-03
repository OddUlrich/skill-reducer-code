from __future__ import annotations


def split_items(markdown: str) -> list[str]:
    items: list[str] = []
    buf: list[str] = []
    in_code = False
    for line in markdown.splitlines():
        if line.strip().startswith("```"):
            in_code = not in_code
            buf.append(line)
            continue
        if not in_code and not line.strip():
            if buf:
                items.append("\n".join(buf).strip())
                buf = []
            continue
        if not in_code and line.startswith("#"):
            if buf:
                items.append("\n".join(buf).strip())
                buf = []
            buf.append(line)
            continue
        buf.append(line)
    if buf:
        items.append("\n".join(buf).strip())
    return [item for item in items if item]

