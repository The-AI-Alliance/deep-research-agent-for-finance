# Common path and file utilities

import os
from pathlib import Path, PosixPath

def cwd() -> Path:
    """Return the real path to the current working directory, which can be changed by an application!"""
    return Path(os.path.realpath('.'))

def this_files_directory(file: str|Path = __file__) -> Path:
    return os.path.dirname(os.path.realpath(file))

def resolve_path(path_str: str, possible_parent: Path) -> Path:
    """
    If the input `path_str` contains a directory prefix, then return it as a `Path`.
    If it doesn't contain a directory prefix, return a Path with `possible_parent` as
    the directory part.

    Args:
        path_str (str): A path that may or may not contain a directory prefix.
        possible_parent (Path): If not None, use this parent path if `path_str` doesn't contain a directory prefix.

    Returns:
        The resolved path, whether or not it a actualy exists!
    """
    path = Path(path_str)
    if not len(path.parents) or path.parents[0] == PosixPath('.'):
        if possible_parent:
            path = possible_parent / path
    return path

def resolve_and_require_path(path_str: str, possible_parent: Path, raise_on_missing: bool = True) -> Path:
    """
    If the input `path_str` contains a directory prefix, then return it as a `Path`.
    If it doesn't contain a directory prefix, return a Path with `possible_parent` as
    the directory part.

    Args:
        path_str (str): A path that may or may not contain a directory prefix.
        possible_parent (Path): If not None, use this parent path is `path_str` doesn't contain a directory prefix.
        raise_on_missing (bool): If `True` and the resolved path doesn't exist, raise a `ValueError`. If `False`, return `None`.

    Returns:
        The resolved path or None if the path doesn't exist, but `raise_on_missing` is `False`.
    """
    path = resolve_path(path_str, possible_parent)
    if not path.exists():
        if raise_on_missing:
            raise ValueError(f"Resolved path '{path}' doesn't exist!")
        path = None
    return path
