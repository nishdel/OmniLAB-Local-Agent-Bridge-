"""Read only explicitly selected regular text files beneath a configured root."""
from pathlib import Path
import stat
from .bridge import BridgeError


def resolve_selected(root, name):
    path = Path(name)
    if path.is_absolute() or path.drive or ".." in path.parts or ":" in name or "\\\\" in name:
        raise BridgeError("Select relative paths within source_root; traversal and alternate streams are forbidden.")
    selected = root / path
    for component in (selected, *selected.parents):
        if component == root:
            break
        info = component.lstat()
        if component.is_symlink() or getattr(info, "st_file_attributes", 0) & 0x400:
            raise BridgeError("Selected files may not pass through symlinks or junctions.")
    resolved = selected.resolve(strict=True)
    if not resolved.is_relative_to(root) or not stat.S_ISREG(resolved.stat().st_mode):
        raise BridgeError("Select regular text files within source_root.")
    return resolved


def read_selected(config, paths):
    if not paths:
        return ""
    if config.source_root is None:
        raise BridgeError("File selection is disabled. Configure source_root or supply file contents.")
    if len(paths) > 20:
        raise BridgeError("Select at most 20 files.")
    root = config.source_root
    result = []
    remaining = config.max_input_chars
    for name in paths:
        try:
            resolved = resolve_selected(root, name)
            with resolved.open("rb") as f:
                raw = f.read(remaining + 1)
            if len(raw) > remaining:
                raise BridgeError("Selected files exceed the input budget. Select smaller files or provide excerpts.")
            if b"\0" in raw:
                raise BridgeError("Selected files must be UTF-8 text.")
            content = raw.decode("utf-8-sig")
            result.append(f"FILE {name}\n{content}")
            remaining -= len(raw) + len(name) + 7
            if remaining < 0:
                raise BridgeError("Selected files exceed the input budget.")
        except (OSError, UnicodeError, ValueError):
            raise BridgeError("Cannot read a selected UTF-8 file within source_root.") from None
    return "\n".join(result)
