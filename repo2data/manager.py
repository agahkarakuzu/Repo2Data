"""Dataset manager for orchestrating downloads."""

import os
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
import logging

from rich.panel import Panel
from rich.tree import Tree

from repo2data.config.loader import ConfigLoader
from repo2data.config.validator import ConfigValidator
from repo2data.downloader import DatasetDownloader
from repo2data.utils.logger import get_logger, console

logger = logging.getLogger(__name__)


def _get_directory_size(path: Path) -> int:
    """Calculate total size of directory in bytes."""
    total = 0
    try:
        for entry in path.rglob('*'):
            if entry.is_file():
                total += entry.stat().st_size
    except Exception:
        pass
    return total


def _format_size(size_bytes: int) -> str:
    """Format bytes to human-readable size."""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f} PB"


def _build_directory_tree(path: Path, max_depth: int = 2, max_files: int = 10) -> Tree:
    """Build a rich Tree showing directory structure."""
    tree = Tree(f"[bold cyan]{path.name}/[/bold cyan]")

    def add_children(parent_tree: Tree, parent_path: Path, current_depth: int):
        if current_depth >= max_depth:
            return

        try:
            items = sorted(parent_path.iterdir(), key=lambda x: (not x.is_dir(), x.name))
            file_count = 0

            for item in items:
                if item.is_dir():
                    subtree = parent_tree.add(f"[cyan]{item.name}/[/cyan]")
                    add_children(subtree, item, current_depth + 1)
                else:
                    if file_count < max_files:
                        size = item.stat().st_size
                        parent_tree.add(f"[dim]{item.name}[/dim] [yellow]({_format_size(size)})[/yellow]")
                        file_count += 1

            if file_count == max_files and len([x for x in items if x.is_file()]) > max_files:
                remaining = len([x for x in items if x.is_file()]) - max_files
                parent_tree.add(f"[dim]... and {remaining} more file(s)[/dim]")

        except PermissionError:
            pass

    add_children(tree, path, 0)
    return tree


class DatasetManager:
    """
    Manages dataset downloads from requirement files.

    Orchestrates loading configuration, validating it, and coordinating
    multiple downloads. Replaces the old Repo2Data class.
    """

    def __init__(
        self,
        requirement_path: Optional[str] = None,
        server_mode: bool = False,
        server_destination: str = "./data"
    ):
        """
        Initialize DatasetManager.

        Parameters
        ----------
        requirement_path : str, optional
            Path to requirement file (JSON/YAML) or GitHub URL.
            Defaults to './data_requirement.json'
        server_mode : bool
            If True, force all downloads to server_destination
        server_destination : str
            Destination directory when in server mode
        """
        self.requirement_path = requirement_path
        self.server_mode = server_mode
        self.server_destination = server_destination
        self.logger = get_logger(__name__)

        # Load and validate configuration
        self.config_loader = ConfigLoader(requirement_path)
        self.config_validator = ConfigValidator()
        self.requirements: Optional[Dict[str, Any]] = None

    def load_requirements(self) -> Dict[str, Any]:
        """
        Load and validate requirements.

        Returns
        -------
        dict
            Loaded requirements

        Raises
        ------
        ValueError
            If requirements are invalid
        """
        # Load configuration
        self.requirements = self.config_loader.load()

        # Validate configuration
        try:
            self.config_validator.validate(self.requirements)
        except ValueError as e:
            self.logger.error(f"Invalid configuration: {e}")
            raise

        return self.requirements

    def install(self) -> List[str]:
        """
        Install all datasets defined in requirements.

        Returns
        -------
        list of str
            Paths to installed datasets

        Examples
        --------
        >>> manager = DatasetManager("data_requirement.json")
        >>> paths = manager.install()
        >>> print(paths)
        ['./data/dataset1', './data/dataset2']
        """
        # Load requirements if not already loaded
        if self.requirements is None:
            self.load_requirements()

        # Parse and execute downloads
        downloads = self._parse_requirements()

        # Build header with source info
        config_name = Path(self.config_loader.config_path).name
        download_count = len(downloads)

        # Get first source for display
        first_config = next(iter(downloads.values()))
        first_src = first_config.get('src', '')
        if len(first_src) > 50:
            first_src = first_src[:47] + "..."

        # Create informative header
        header_text = f"[dim]config:[/dim] {config_name}\n"
        header_text += f"[dim]downloads:[/dim] {download_count}"
        if download_count == 1:
            header_text += f"\n[dim]source:[/dim] {first_src}"

        # Show header
        console.print()
        console.print(Panel.fit(header_text, title="repo2data", border_style="cyan"))

        results = []

        # Process downloads
        for idx, (download_key, config) in enumerate(downloads.items(), 1):
            project_name = config.get('projectName', 'unknown')
            display_name = download_key or project_name

            console.print(
                f"\n[cyan]({idx}/{len(downloads)})[/cyan] "
                f"[bold]{display_name}[/bold]"
            )

            try:
                downloader = DatasetDownloader(
                    config=config,
                    server_mode=self.server_mode,
                    server_destination=self.server_destination,
                    requirement_path=self.config_loader.config_path,
                    download_key=download_key
                )

                result_path = downloader.download()
                results.append(result_path)

                console.print(
                    f"  [green]✓[/green] Downloaded to [bright_yellow]{result_path}[/bright_yellow]"
                )

            except Exception as e:
                console.print(f"  [red]✗[/red] {str(e)}")
                # Continue with other downloads
                continue

        # Show summary with details
        console.print()
        if results:
            # Calculate total size
            total_size = sum(_get_directory_size(Path(p)) for p in results)

            # Build summary panel
            summary = f"[bold green]✓ {len(results)}/{len(downloads)} dataset(s) downloaded[/bold green]\n"
            summary += f"[dim]Total size:[/dim] {_format_size(total_size)}\n"

            if len(results) == 1:
                summary += f"[dim]Location:[/dim] {results[0]}"
            else:
                summary += f"[dim]Locations:[/dim]\n"
                for result_path in results:
                    summary += f"  • {result_path}\n"

            console.print(Panel.fit(summary.rstrip(), border_style="green", title="Summary"))

            # Show directory tree for each download
            for result_path in results:
                path = Path(result_path)
                if path.exists():
                    console.print()
                    tree = _build_directory_tree(path)
                    console.print(Panel.fit(tree, border_style="plum1", title=f"Content tree"))
        else:
            console.print(Panel.fit(
                f"[bold red]✗ No datasets downloaded[/bold red]",
                border_style="red"
            ))
        console.print()

        return results

    def _parse_requirements(self) -> Dict[Optional[str], Dict[str, Any]]:
        """
        Parse requirements into individual download configurations.

        Returns
        -------
        dict
            Dictionary mapping download keys to configurations.
            For single downloads, key is None.

        Examples
        --------
        Single download:
        {None: {"src": "...", "projectName": "..."}}

        Multiple downloads:
        {"dataset1": {"src": "...", "projectName": "..."},
         "dataset2": {"src": "...", "projectName": "..."}}
        """
        if not self.requirements:
            raise ValueError("Requirements not loaded")

        # Detect single vs multi-download
        first_key = next(iter(self.requirements))
        first_value = self.requirements[first_key]

        if isinstance(first_value, dict):
            # Multi-download configuration
            downloads = {}
            for key, value in self.requirements.items():
                if isinstance(value, dict):
                    downloads[key] = value
            return downloads
        else:
            # Single download configuration
            return {None: self.requirements}

    def get_download_info(self) -> Dict[str, Any]:
        """
        Get information about configured downloads.

        Returns
        -------
        dict
            Information about downloads

        Examples
        --------
        >>> manager = DatasetManager("data_requirement.json")
        >>> info = manager.get_download_info()
        >>> print(info['count'])
        2
        """
        if self.requirements is None:
            self.load_requirements()

        downloads = self._parse_requirements()

        info = {
            "count": len(downloads),
            "downloads": {}
        }

        for key, config in downloads.items():
            download_key = key or "default"
            info["downloads"][download_key] = {
                "source": config.get("src", ""),
                "project": config.get("projectName", ""),
                "destination": config.get("dst", "")
            }

        return info

    def __repr__(self) -> str:
        """String representation."""
        return (
            f"DatasetManager("
            f"requirement_path={self.requirement_path}, "
            f"server_mode={self.server_mode})"
        )
