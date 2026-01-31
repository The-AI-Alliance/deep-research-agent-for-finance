# Common path and file utilities

from pathlib import Path, PosixPath

def resolve_path(path_str: str, possible_parent: Path) -> Path:
    """
    If the input `path_str` contains a directory prefix, then return it as a `Path`.
    If it doesn't contain a directory prefix, return a Path with `possible_parent` as
    the directory part.
    """
    path = Path(path_str)
    if path.parents[0] == PosixPath('.'):
        return possible_parent / path
    else:
        return path
