"""
Example usage of locate_evidence_data for finding datasets in notebooks.

This demonstrates how to use the data locator from notebooks in nested
directories, following the evidence/neurolibre convention where data is
stored at <repo_root>/data/<project_name>.
"""

from repo2data import locate_evidence_data, list_evidence_datasets
from pathlib import Path


def example_basic_usage():
    """Basic usage: locate a specific dataset."""
    print("=" * 60)
    print("Example 1: Basic Usage - Locate Specific Dataset")
    print("=" * 60)

    # Works from any nested directory in the repository
    # The function traverses upward to find myst.yml, then constructs the data path
    data_path = locate_evidence_data("my_dataset", verify_exists=False)

    print(f"Dataset path: {data_path}")
    print(f"Expected: <repo_root>/data/my_dataset")
    print()


def example_auto_detect():
    """Auto-detect project name from config file."""
    print("=" * 60)
    print("Example 2: Auto-detect Project Name from myst.yml")
    print("=" * 60)

    # If project_name is not provided, it reads from the config file
    data_path = locate_evidence_data(verify_exists=False)

    print(f"Auto-detected dataset path: {data_path}")
    print("Project name read from data.projectName in myst.yml")
    print()


def example_list_datasets():
    """List all available datasets."""
    print("=" * 60)
    print("Example 3: List All Available Datasets")
    print("=" * 60)

    datasets = list_evidence_datasets()

    if datasets:
        print(f"Found {len(datasets)} dataset(s):")
        for ds in datasets:
            print(f"  - {ds}")
    else:
        print("No datasets found (data directory may not exist yet)")
    print()


def example_notebook_workflow():
    """Typical workflow in a notebook."""
    print("=" * 60)
    print("Example 4: Typical Notebook Workflow")
    print("=" * 60)

    # Step 1: Locate your data
    data_path = locate_evidence_data("my_analysis_data", verify_exists=False)
    print(f"1. Located data at: {data_path}")

    # Step 2: Use the path to load your data
    # In a real notebook, you might do:
    # import pandas as pd
    # df = pd.read_csv(data_path / "results.csv")
    # import numpy as np
    # data = np.load(data_path / "array.npy")

    print("2. Load data using the path:")
    print(f"   df = pd.read_csv({data_path / 'results.csv'})")
    print(f"   data = np.load({data_path / 'array.npy'})")
    print()


def example_custom_config():
    """Use custom config file."""
    print("=" * 60)
    print("Example 5: Custom Config File")
    print("=" * 60)

    # You can specify different config files to search for
    data_path = locate_evidence_data(
        "my_dataset",
        config_files=["data_requirement.yaml", "myst.yml"],
        verify_exists=False
    )

    print(f"Dataset path: {data_path}")
    print("Searched for: data_requirement.yaml first, then myst.yml")
    print()


def example_error_handling():
    """Error handling examples."""
    print("=" * 60)
    print("Example 6: Error Handling")
    print("=" * 60)

    # Handling missing config file
    try:
        # This would fail if no config file exists
        data_path = locate_evidence_data(
            "my_dataset",
            start_dir="/tmp/nonexistent",
            verify_exists=False
        )
    except FileNotFoundError as e:
        print(f"✓ Caught expected error: Config file not found")
        print(f"  (This is expected when no myst.yml exists)")

    # Handling non-existent data path
    try:
        # This would fail if data path doesn't exist and verify_exists=True
        data_path = locate_evidence_data(
            "nonexistent_dataset",
            verify_exists=True  # Will check if path exists
        )
    except FileNotFoundError as e:
        print(f"✓ Caught expected error: Data path doesn't exist")
        print(f"  (Use verify_exists=False to skip this check)")

    print()


if __name__ == "__main__":
    print("\n")
    print("╔" + "=" * 58 + "╗")
    print("║" + " " * 12 + "Evidence Data Locator Examples" + " " * 16 + "║")
    print("╚" + "=" * 58 + "╝")
    print()

    example_basic_usage()
    example_auto_detect()
    example_list_datasets()
    example_notebook_workflow()
    example_custom_config()
    example_error_handling()

    print("=" * 60)
    print("All examples completed!")
    print("=" * 60)
    print()
    print("Key Benefits:")
    print("  ✓ No hardcoded paths in notebooks")
    print("  ✓ Works from any nested directory")
    print("  ✓ Follows evidence/neurolibre conventions")
    print("  ✓ Simple, one-line API")
    print()
