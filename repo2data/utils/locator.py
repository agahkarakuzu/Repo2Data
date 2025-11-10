"""Data locator for finding datasets following evidence/neurolibre conventions."""

import os
from pathlib import Path
from typing import Optional, List, Union
import yaml


def locate_evidence_data(
    project_name: Optional[str] = None,
    start_dir: Optional[Union[str, Path]] = None,
    config_files: Optional[List[str]] = None,
    verify_exists: bool = True
) -> Path:
    """
    Locate dataset following evidence/neurolibre convention.

    Traverses upward from current directory (or start_dir) until a config file
    (myst.yml by default) is found, then returns: <repo_root>/data/<project_name>

    This follows the evidence/neurolibre pattern where data is stored at the
    repository root in a 'data' directory, making it easy for notebooks in
    nested directories to find their datasets.

    Parameters
    ----------
    project_name : str, optional
        Name of the dataset (e.g., "my_dataset"). If None, attempts to
        auto-detect from the config file's 'data.projectName' field.
    start_dir : str or Path, optional
        Directory to start search from. Defaults to current working directory.
    config_files : list of str, optional
        Config filenames to search for in order of priority.
        Default: ["myst.yml", "data_requirement.yaml", "data_requirement.json"]
    verify_exists : bool, optional
        If True, raise error if data path doesn't exist. Default: True

    Returns
    -------
    Path
        Absolute path to data directory

    Raises
    ------
    FileNotFoundError
        If config file not found or data path doesn't exist (when verify_exists=True)
    ValueError
        If project_name is None and cannot be auto-detected from config

    Examples
    --------
    >>> # From notebook at: repo/content/notebooks/analysis.ipynb
    >>> data_path = locate_evidence_data("my_dataset")
    >>> # Returns: /absolute/path/to/repo/data/my_dataset
    >>>
    >>> # Auto-detect project name from myst.yml
    >>> data_path = locate_evidence_data()
    >>>
    >>> # Use without verifying existence (useful for creating new directories)
    >>> data_path = locate_evidence_data("new_dataset", verify_exists=False)
    >>> data_path.mkdir(parents=True, exist_ok=True)

    Notes
    -----
    The function searches upward through parent directories until it finds
    a config file. This makes it work reliably from notebooks at any depth
    in the repository structure.
    """
    # Default config files to search for
    if config_files is None:
        config_files = ["myst.yml", "data_requirement.yaml", "data_requirement.json"]

    # Determine starting directory
    if start_dir is None:
        current_dir = Path.cwd()
    else:
        current_dir = Path(start_dir).resolve()

    # Find config file by traversing upward
    config_path = None
    search_dir = current_dir

    # Prevent infinite loop by tracking filesystem root
    root = Path(search_dir.anchor)

    while search_dir != root.parent:
        # Check for each config file
        for config_file in config_files:
            candidate = search_dir / config_file
            if candidate.exists():
                config_path = candidate
                break

        if config_path:
            break

        # Move up one directory
        search_dir = search_dir.parent

    if config_path is None:
        config_list = ", ".join(config_files)
        raise FileNotFoundError(
            f"Could not find config file ({config_list}) in current directory "
            f"or any parent directory.\n"
            f"Started search from: {current_dir}\n\n"
            f"Evidence/neurolibre convention requires a config file at the "
            f"repository root."
        )

    # Get repository root (directory containing config file)
    repo_root = config_path.parent

    # Auto-detect project_name if not provided
    if project_name is None:
        project_name = _extract_project_name(config_path)
        if project_name is None:
            raise ValueError(
                f"project_name not provided and could not be auto-detected from "
                f"{config_path.name}.\n"
                f"Please provide project_name explicitly or ensure your config "
                f"file has a 'data.projectName' field."
            )

    # Construct data path following evidence convention: <repo_root>/data/<project_name>
    data_path = repo_root / "data" / project_name

    # Verify existence if requested
    if verify_exists and not data_path.exists():
        raise FileNotFoundError(
            f"Data directory not found: {data_path}\n\n"
            f"Expected location following evidence/neurolibre convention:\n"
            f"  Repository root: {repo_root}\n"
            f"  Data directory: {data_path}\n\n"
            f"If you want to locate a path without verifying its existence, "
            f"use verify_exists=False"
        )

    return data_path.resolve()


def list_evidence_datasets(
    start_dir: Optional[Union[str, Path]] = None,
    config_files: Optional[List[str]] = None
) -> List[str]:
    """
    List all datasets in the evidence data directory.

    Finds the repository root (by locating config file) and lists all
    subdirectories in the data/ folder.

    Parameters
    ----------
    start_dir : str or Path, optional
        Directory to start search from. Defaults to current working directory.
    config_files : list of str, optional
        Config filenames to search for in order of priority.
        Default: ["myst.yml", "data_requirement.yaml", "data_requirement.json"]

    Returns
    -------
    list of str
        Names of all subdirectories in data/

    Raises
    ------
    FileNotFoundError
        If config file not found or data directory doesn't exist

    Examples
    --------
    >>> datasets = list_evidence_datasets()
    >>> print(datasets)
    ['dataset1', 'dataset2', 'my_analysis_data']
    """
    # Default config files
    if config_files is None:
        config_files = ["myst.yml", "data_requirement.yaml", "data_requirement.json"]

    # Determine starting directory
    if start_dir is None:
        current_dir = Path.cwd()
    else:
        current_dir = Path(start_dir).resolve()

    # Find config file by traversing upward
    config_path = None
    search_dir = current_dir
    root = Path(search_dir.anchor)

    while search_dir != root.parent:
        for config_file in config_files:
            candidate = search_dir / config_file
            if candidate.exists():
                config_path = candidate
                break

        if config_path:
            break

        search_dir = search_dir.parent

    if config_path is None:
        config_list = ", ".join(config_files)
        raise FileNotFoundError(
            f"Could not find config file ({config_list}) in current directory "
            f"or any parent directory.\n"
            f"Started search from: {current_dir}"
        )

    # Get repository root and data directory
    repo_root = config_path.parent
    data_dir = repo_root / "data"

    if not data_dir.exists():
        return []

    # List all subdirectories
    datasets = []
    try:
        for item in data_dir.iterdir():
            if item.is_dir():
                datasets.append(item.name)
    except PermissionError:
        pass

    return sorted(datasets)


def _extract_project_name(config_path: Path) -> Optional[str]:
    """
    Extract project name from config file with multiple fallback strategies.

    Tries in order:
    1. data.projectName from config file (myst.yml or data_requirement.yaml)
    2. projectName from top-level of data_requirement.json/yaml
    3. binder/data_requirement.txt in same directory
    4. Infer from project.github in myst.yml

    Parameters
    ----------
    config_path : Path
        Path to config file

    Returns
    -------
    str or None
        Project name if found, None otherwise
    """
    import re
    import json

    repo_root = config_path.parent

    try:
        # Load config file
        if config_path.suffix in ['.yml', '.yaml']:
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)
        elif config_path.suffix == '.json':
            with open(config_path, 'r') as f:
                config = json.load(f)
        else:
            config = None

        if isinstance(config, dict):
            # Strategy 1: Try data.projectName (myst.yml pattern)
            data_section = config.get('data', {})
            if isinstance(data_section, dict):
                project_name = data_section.get('projectName')
                if project_name:
                    return project_name

            # Strategy 2: Try top-level projectName (data_requirement.json/yaml pattern)
            project_name = config.get('projectName')
            if project_name:
                return project_name

            # Strategy 3: Infer from project.github in myst.yml
            if config_path.name == 'myst.yml' or 'myst' in config_path.name.lower():
                project_metadata = config.get('project', {})
                if isinstance(project_metadata, dict):
                    github_url = project_metadata.get('github', '')
                    if github_url:
                        # Extract from GitHub URL pattern
                        match = re.search(r'github\.com/([^/]+)/([^/\s]+)', github_url)
                        if match:
                            username, repo = match.groups()
                            repo = repo.rstrip('.git')
                            return f"{username}_{repo}".lower()

    except Exception:
        pass

    # Strategy 4: Check binder/data_requirement.txt
    try:
        binder_req = repo_root / 'binder' / 'data_requirement.txt'
        if binder_req.exists():
            with open(binder_req, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        # Try to parse as JSON
                        try:
                            req_data = json.loads(line)
                            if isinstance(req_data, dict):
                                project_name = req_data.get('projectName')
                                if project_name:
                                    return project_name
                        except json.JSONDecodeError:
                            pass
    except Exception:
        pass

    return None
