#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Command-line interface for repo2data.

Provides CLI access to DatasetManager for downloading datasets
from requirement files (JSON or YAML).
"""

import argparse
import sys
import logging
from pathlib import Path
from datetime import datetime

from repo2data import DatasetManager, __version__, GlobalCacheManager, get_cache_dir, CacheMigrator
from repo2data.utils.logger import setup_logger
from rich.table import Table
from rich.panel import Panel
from repo2data.utils.logger import console


def get_parser() -> argparse.ArgumentParser:
    """
    Create argument parser for repo2data CLI.

    Returns
    -------
    argparse.ArgumentParser
        Configured argument parser
    """
    parser = argparse.ArgumentParser(
        prog="repo2data",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description="Download datasets from various sources with caching",
        epilog="""
Examples:
  # Download using default data_requirement.json in current directory
  repo2data

  # Download using specific JSON file
  repo2data -r path/to/data_requirement.json

  # Download using YAML file
  repo2data -r path/to/data_requirement.yaml

  # Download from GitHub repository
  repo2data -r https://github.com/user/repo

  # Force destination directory (server mode)
  repo2data --server --destination ./my_data

  # Enable debug logging
  repo2data -r config.yaml --log-level DEBUG

  # Cache management
  repo2data cache list               # List all cached datasets
  repo2data cache info               # Show cache statistics
  repo2data cache verify             # Verify cache integrity
  repo2data cache clean              # Remove orphaned cache entries
  repo2data cache remove <project>   # Remove specific cache entry
  repo2data cache clear              # Clear all cache entries
  repo2data cache migrate /path      # Migrate old local caches to global cache

Documentation: https://github.com/SIMEXP/Repo2Data
        """
    )

    # Add subparsers for cache commands
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")

    # Cache command
    cache_parser = subparsers.add_parser(
        "cache",
        help="Manage global cache",
        description="Manage the global repo2data cache"
    )
    cache_subparsers = cache_parser.add_subparsers(
        dest="cache_command",
        help="Cache management command"
    )

    # cache list
    list_parser = cache_subparsers.add_parser(
        "list",
        help="List all cached datasets"
    )
    list_parser.add_argument(
        "--sort",
        choices=["name", "size", "date"],
        default="date",
        help="Sort by name, size, or date. Default: date"
    )

    # cache clean
    clean_parser = cache_subparsers.add_parser(
        "clean",
        help="Remove orphaned cache entries"
    )

    # cache verify
    verify_parser = cache_subparsers.add_parser(
        "verify",
        help="Verify cache integrity"
    )

    # cache clear
    clear_parser = cache_subparsers.add_parser(
        "clear",
        help="Clear all cache entries (does not delete data files)"
    )
    clear_parser.add_argument(
        "--confirm",
        action="store_true",
        help="Confirm cache clear without prompting"
    )

    # cache info
    info_parser = cache_subparsers.add_parser(
        "info",
        help="Show cache statistics"
    )

    # cache migrate
    migrate_parser = cache_subparsers.add_parser(
        "migrate",
        help="Migrate local cache files to global cache"
    )
    migrate_parser.add_argument(
        "paths",
        nargs="*",
        help="Directories to search for local cache files (default: current directory)"
    )
    migrate_parser.add_argument(
        "--remove",
        action="store_true",
        help="Remove local cache files after successful migration"
    )

    # cache remove
    remove_parser = cache_subparsers.add_parser(
        "remove",
        help="Remove cache entry by project name or path"
    )
    remove_parser.add_argument(
        "identifier",
        help="Project name or destination path to remove"
    )
    remove_parser.add_argument(
        "--path",
        action="store_true",
        help="Treat identifier as a path instead of project name"
    )

    parser.add_argument(
        "-r", "--requirement",
        dest="requirement",
        required=False,
        default=None,
        metavar="PATH",
        help=(
            "Path to data requirement file (JSON/YAML) or GitHub repo URL. "
            "Default: ./data_requirement.json"
        )
    )

    parser.add_argument(
        "--server",
        action="store_true",
        required=False,
        default=False,
        help="Enable server mode (force destination directory)"
    )

    parser.add_argument(
        "--destination",
        dest="destination",
        required=False,
        default="./data",
        metavar="DIR",
        help="Destination directory for server mode. Default: ./data"
    )

    parser.add_argument(
        "-l", "--log-level",
        dest="log_level",
        required=False,
        default="WARNING",  # Changed from INFO to WARNING for cleaner output
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        help="Set logging level. Default: WARNING"
    )

    parser.add_argument(
        "--log-file",
        dest="log_file",
        required=False,
        default=None,
        metavar="FILE",
        help="Write logs to file in addition to console"
    )

    parser.add_argument(
        "-v", "--version",
        action="version",
        version=f"repo2data {__version__}"
    )

    return parser


def _format_size(size_bytes: int) -> str:
    """Format bytes to human-readable size."""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f} PB"


def _format_timestamp(timestamp_str: str) -> str:
    """Format ISO timestamp to relative time."""
    try:
        dt = datetime.fromisoformat(timestamp_str)
        now = datetime.now()
        delta = now - dt

        if delta.days > 365:
            years = delta.days // 365
            return f"{years} year{'s' if years > 1 else ''} ago"
        elif delta.days > 30:
            months = delta.days // 30
            return f"{months} month{'s' if months > 1 else ''} ago"
        elif delta.days > 0:
            return f"{delta.days} day{'s' if delta.days > 1 else ''} ago"
        elif delta.seconds > 3600:
            hours = delta.seconds // 3600
            return f"{hours} hour{'s' if hours > 1 else ''} ago"
        elif delta.seconds > 60:
            minutes = delta.seconds // 60
            return f"{minutes} minute{'s' if minutes > 1 else ''} ago"
        else:
            return "just now"
    except:
        return timestamp_str


def cache_list_command(args) -> int:
    """Handle 'cache list' command."""
    cache = GlobalCacheManager()
    entries = cache.list_all_cached()

    if not entries:
        console.print(Panel(
            "[yellow]No cached datasets found[/yellow]",
            title="Cache",
            border_style="yellow"
        ))
        return 0

    # Sort entries
    if args.sort == "name":
        entries.sort(key=lambda x: x['config'].get('projectName', ''))
    elif args.sort == "size":
        entries.sort(key=lambda x: x['size_bytes'], reverse=True)
    else:  # date
        entries.sort(key=lambda x: x['last_accessed'], reverse=True)

    # Create table
    table = Table(title=f"Cached Datasets ({len(entries)} total)", show_header=True)
    table.add_column("Project", style="cyan", no_wrap=True)
    table.add_column("Size", style="yellow", justify="right")
    table.add_column("Files", justify="right")
    table.add_column("Last Accessed", style="dim")
    table.add_column("Location", style="dim", overflow="fold")
    table.add_column("Status", justify="center")

    total_size = 0
    for entry in entries:
        project_name = entry['config'].get('projectName', 'unknown')
        size = entry['size_bytes']
        file_count = entry['file_count']
        last_accessed = _format_timestamp(entry['last_accessed'])
        location = entry['destination_path']
        exists = entry['exists']
        status = "[green]✓[/green]" if exists else "[red]✗[/red]"

        table.add_row(
            project_name,
            _format_size(size),
            str(file_count),
            last_accessed,
            location,
            status
        )
        total_size += size

    console.print()
    console.print(table)
    console.print()
    console.print(f"[dim]Total cache size: {_format_size(total_size)}[/dim]")
    console.print(f"[dim]Cache location: {get_cache_dir()}[/dim]")
    console.print()

    return 0


def cache_clean_command(args) -> int:
    """Handle 'cache clean' command."""
    cache = GlobalCacheManager()

    console.print()
    console.print("[cyan]Cleaning orphaned cache entries...[/cyan]")

    removed = cache.clean_orphaned_entries()

    if removed > 0:
        console.print(Panel(
            f"[green]✓ Removed {removed} orphaned cache entr{'ies' if removed > 1 else 'y'}[/green]",
            border_style="green"
        ))
    else:
        console.print(Panel(
            "[green]✓ No orphaned cache entries found[/green]",
            border_style="green"
        ))

    console.print()
    return 0


def cache_verify_command(args) -> int:
    """Handle 'cache verify' command."""
    cache = GlobalCacheManager()
    entries = cache.list_all_cached()

    if not entries:
        console.print(Panel(
            "[yellow]No cached datasets to verify[/yellow]",
            title="Cache Verification",
            border_style="yellow"
        ))
        return 0

    console.print()
    console.print(f"[cyan]Verifying {len(entries)} cached dataset(s)...[/cyan]")
    console.print()

    valid = 0
    invalid = 0

    for entry in entries:
        project_name = entry['config'].get('projectName', 'unknown')
        path = Path(entry['destination_path'])

        if path.exists():
            console.print(f"  [green]✓[/green] {project_name} - [dim]{path}[/dim]")
            valid += 1
        else:
            console.print(f"  [red]✗[/red] {project_name} - [red]Missing:[/red] [dim]{path}[/dim]")
            invalid += 1

    console.print()

    if invalid > 0:
        console.print(Panel(
            f"[yellow]⚠ {invalid} dataset(s) missing on disk[/yellow]\n\n"
            f"Run [bold]repo2data cache clean[/bold] to remove orphaned entries",
            title="Verification Results",
            border_style="yellow"
        ))
    else:
        console.print(Panel(
            f"[green]✓ All {valid} cached dataset(s) verified[/green]",
            title="Verification Results",
            border_style="green"
        ))

    console.print()
    return 0


def cache_clear_command(args) -> int:
    """Handle 'cache clear' command."""
    cache = GlobalCacheManager()
    entries = cache.list_all_cached()

    if not entries:
        console.print(Panel(
            "[yellow]Cache is already empty[/yellow]",
            title="Cache",
            border_style="yellow"
        ))
        return 0

    # Confirm if not already confirmed
    if not args.confirm:
        console.print()
        console.print(f"[yellow]This will clear {len(entries)} cache entr{'ies' if len(entries) > 1 else 'y'}[/yellow]")
        console.print("[dim](Data files will NOT be deleted)[/dim]")
        console.print()
        response = input("Continue? [y/N]: ")
        if response.lower() not in ('y', 'yes'):
            console.print("[yellow]Cancelled[/yellow]")
            return 0

    console.print()
    console.print("[cyan]Clearing cache...[/cyan]")

    cleared = cache.clear_all()

    console.print(Panel(
        f"[green]✓ Cleared {cleared} cache entr{'ies' if cleared > 1 else 'y'}[/green]",
        border_style="green"
    ))
    console.print()

    return 0


def cache_info_command(args) -> int:
    """Handle 'cache info' command."""
    cache = GlobalCacheManager()
    entries = cache.list_all_cached()

    if not entries:
        console.print(Panel(
            "[yellow]Cache is empty[/yellow]",
            title="Cache Statistics",
            border_style="yellow"
        ))
        return 0

    total_size = cache.get_total_cache_size()
    total_files = sum(e['file_count'] for e in entries)
    valid = sum(1 for e in entries if e['exists'])
    invalid = len(entries) - valid

    # Calculate age statistics
    now = datetime.now()
    ages = []
    for e in entries:
        try:
            dt = datetime.fromisoformat(e['last_accessed'])
            ages.append((now - dt).days)
        except:
            pass

    avg_age = sum(ages) / len(ages) if ages else 0

    info_text = f"""[bold cyan]Total Datasets:[/bold cyan] {len(entries)}
[bold cyan]Total Size:[/bold cyan] {_format_size(total_size)}
[bold cyan]Total Files:[/bold cyan] {total_files:,}
[bold cyan]Valid Entries:[/bold cyan] {valid}
[bold cyan]Orphaned Entries:[/bold cyan] {invalid}
[bold cyan]Average Age:[/bold cyan] {int(avg_age)} days
[bold cyan]Cache Location:[/bold cyan] {get_cache_dir()}"""

    console.print()
    console.print(Panel(
        info_text,
        title="Cache Statistics",
        border_style="cyan"
    ))
    console.print()

    return 0


def cache_migrate_command(args) -> int:
    """Handle 'cache migrate' command."""
    cache = GlobalCacheManager()
    migrator = CacheMigrator(cache)

    # Determine search paths
    if args.paths:
        search_paths = [Path(p).resolve() for p in args.paths]
    else:
        search_paths = [Path.cwd()]

    console.print()
    console.print(f"[cyan]Searching for local cache files in {len(search_paths)} location(s)...[/cyan]")
    console.print()

    # Find all local cache files
    cache_files = migrator.find_local_caches(search_paths)

    if not cache_files:
        console.print(Panel(
            "[yellow]No local cache files found[/yellow]\n\n"
            "[dim]Local cache files are named 'repo2data_cache.json' or '*_repo2data_cache.json'[/dim]",
            title="Migration",
            border_style="yellow"
        ))
        return 0

    console.print(f"[cyan]Found {len(cache_files)} local cache file(s)[/cyan]")
    console.print()

    # Show files to be migrated
    for cache_file in cache_files[:10]:  # Show first 10
        console.print(f"  [dim]• {cache_file}[/dim]")
    if len(cache_files) > 10:
        console.print(f"  [dim]... and {len(cache_files) - 10} more[/dim]")

    console.print()

    # Migrate
    console.print("[cyan]Migrating to global cache...[/cyan]")
    migrated, failed = migrator.migrate_all(search_paths, remove_after=args.remove)

    console.print()

    if migrated > 0:
        action = "migrated and removed" if args.remove else "migrated"
        console.print(Panel(
            f"[green]✓ Successfully {action} {migrated} local cache file(s)[/green]" +
            (f"\n[red]✗ Failed to migrate {failed} file(s)[/red]" if failed > 0 else ""),
            title="Migration Complete",
            border_style="green"
        ))
        console.print()
        console.print(f"[dim]Global cache location: {get_cache_dir()}[/dim]")
    else:
        console.print(Panel(
            "[yellow]No cache files were migrated[/yellow]\n\n"
            "[dim]Cache files may already be migrated or contain invalid data[/dim]",
            title="Migration",
            border_style="yellow"
        ))

    console.print()
    return 0


def cache_remove_command(args) -> int:
    """Handle 'cache remove' command."""
    cache = GlobalCacheManager()

    console.print()

    if args.path:
        # Remove by destination path
        console.print(f"[cyan]Removing cache entry for path: {args.identifier}[/cyan]")
        removed = cache.remove_by_destination(args.identifier)
    else:
        # Remove by project name
        console.print(f"[cyan]Removing cache entries for project: {args.identifier}[/cyan]")
        removed = cache.remove_by_project(args.identifier)

    console.print()

    if removed > 0:
        console.print(Panel(
            f"[green]✓ Removed {removed} cache entr{'ies' if removed > 1 else 'y'}[/green]\n\n"
            "[dim]Data files were NOT deleted[/dim]",
            title="Cache Removed",
            border_style="green"
        ))
    else:
        console.print(Panel(
            f"[yellow]No cache entries found for: {args.identifier}[/yellow]\n\n"
            "[dim]Use 'repo2data cache list' to see all cached datasets[/dim]",
            title="Not Found",
            border_style="yellow"
        ))

    console.print()
    return 0


def main() -> int:
    """
    Main entry point for repo2data CLI.

    Returns
    -------
    int
        Exit code (0 for success, 1 for failure)
    """
    # Parse arguments
    parser = get_parser()
    args = parser.parse_args()

    # Handle cache commands (no logging setup needed for these)
    if args.command == "cache":
        if not args.cache_command:
            parser.print_help()
            return 1

        try:
            if args.cache_command == "list":
                return cache_list_command(args)
            elif args.cache_command == "clean":
                return cache_clean_command(args)
            elif args.cache_command == "verify":
                return cache_verify_command(args)
            elif args.cache_command == "clear":
                return cache_clear_command(args)
            elif args.cache_command == "info":
                return cache_info_command(args)
            elif args.cache_command == "migrate":
                return cache_migrate_command(args)
            elif args.cache_command == "remove":
                return cache_remove_command(args)
            else:
                parser.print_help()
                return 1
        except KeyboardInterrupt:
            console.print("\n[yellow]Interrupted by user[/yellow]")
            return 130
        except Exception as e:
            console.print(f"\n[red]Error:[/red] {e}")
            return 1

    # Setup logging for download commands
    log_level = getattr(logging, args.log_level)
    setup_logger(
        name="repo2data",
        level=log_level,
        log_file=args.log_file if hasattr(args, 'log_file') else None
    )

    logger = logging.getLogger("repo2data.cli")

    try:
        # Create DatasetManager
        manager = DatasetManager(
            requirement_path=args.requirement,
            server_mode=args.server,
            server_destination=args.destination
        )

        # Install datasets
        paths = manager.install()

        # Return exit code based on success
        return 0 if paths else 1

    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        return 1

    except ValueError as e:
        logger.error(f"Configuration error: {e}")
        return 1

    except KeyboardInterrupt:
        logger.warning("\nInterrupted by user")
        return 130

    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=args.log_level == "DEBUG" if hasattr(args, 'log_level') else False)
        return 1


if __name__ == "__main__":
    sys.exit(main())
