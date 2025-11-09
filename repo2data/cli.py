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

from repo2data import DatasetManager, __version__
from repo2data.utils.logger import setup_logger


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

Documentation: https://github.com/SIMEXP/Repo2Data
        """
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
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        help="Set logging level. Default: INFO"
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

    # Setup logging
    log_level = getattr(logging, args.log_level)
    setup_logger(
        name="repo2data",
        level=log_level,
        log_file=args.log_file
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

        # Report success
        if paths:
            logger.info("")
            logger.info("=" * 60)
            logger.info("SUCCESS: All datasets downloaded")
            logger.info("=" * 60)
            for path in paths:
                logger.info(f"  → {path}")
            logger.info("")
            return 0
        else:
            logger.warning("No datasets were downloaded")
            return 1

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
        logger.error(f"Unexpected error: {e}", exc_info=args.log_level == "DEBUG")
        return 1


if __name__ == "__main__":
    sys.exit(main())
