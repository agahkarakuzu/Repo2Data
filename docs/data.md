# Repo2Data Documentation

Welcome to Repo2Data - a flexible data management tool that makes it easy to download, cache, and locate research datasets from multiple sources.

## What is Repo2Data?

Repo2Data is a Python package designed to simplify data management in research projects. It helps you:

- **Download datasets** from multiple providers (Zenodo, Figshare, Dataverse, OSF, Google Drive, etc.)
- **Cache downloads** intelligently to avoid re-downloading data
- **Locate datasets** easily from Jupyter notebooks at any directory depth
- **Verify data integrity** with checksum validation
- **Track downloads** with progress bars and detailed logging

The package follows the **evidence/neurolibre convention** where datasets are stored in a centralized `data/` directory at the repository root, making them accessible from notebooks anywhere in your project.

## Quick Start

### Installation

```bash
pip install repo2data
```

### Basic Usage

Create a configuration file (`myst.yml` or `data_requirement.yaml`):

```yaml
data:
  src: "doi:10.5281/zenodo.6482995"
  dst: "./data"
  projectName: "my_dataset"
```

Download the data:

```bash
repo2data myst.yml
```

Access the data from Python/Jupyter:

```python
from repo2data.utils import locate_evidence_data

# Automatically finds data regardless of current directory
data_path = locate_evidence_data("my_dataset")
print(data_path)  # /absolute/path/to/repo/data/my_dataset
```

## Configuration Fields

Your configuration file uses YAML or JSON format with the following fields:

### Required Fields

- **`src`** (string): Source URL or identifier for the dataset
  - Can be a DOI, URL, or protocol-specific identifier
  - Example: `"doi:10.5281/zenodo.6482995"` or `"https://figshare.com/..."`

- **`dst`** (string): Destination directory where data will be downloaded
  - Can be absolute or relative path
  - Example: `"./data"` or `"/DATA"`

- **`projectName`** (string): Unique identifier for this dataset
  - Used for caching and locating the dataset
  - Creates a subdirectory: `{dst}/{projectName}/`
  - Example: `"my_analysis_data"`

### Optional Fields

- **`version`** (string): Dataset version identifier
  - Used for cache validation - changing this will trigger re-download
  - Example: `"v1.0"` or `"2024-01-15"`

- **`checksum`** (string): Expected checksum hash for verification
  - Validates data integrity after download
  - Example: `"a7b3c4d5e6f7..."`

- **`checksum_algorithm`** (string): Hash algorithm to use
  - Options: `"sha256"` (default), `"md5"`, `"sha1"`
  - Example: `"sha256"`

- **`remote_filepath`** (string or list): Specific files to download (provider-specific)
  - For OSF: Download only specific files instead of entire project
  - Can be a single path or list of paths
  - Example: `"raw_data/experiment1.csv"` or `["file1.csv", "file2.csv"]`

- **`recursive`** (boolean): Enable recursive download (provider-specific)
  - Some providers support recursive subdirectory downloads
  - Default: `false`

## Using Data Locator Utilities

Repo2Data provides utilities to easily locate your datasets from anywhere in your repository - especially useful in Jupyter notebooks!

### `locate_evidence_data()` - Find Your Dataset

This function automatically locates datasets following the evidence/neurolibre convention.

**How it works:**
1. Searches upward from current directory for config file (`myst.yml`, `data_requirement.yaml`, etc.)
2. Returns path to: `<repo_root>/data/<project_name>/`
3. Works from notebooks at any depth in your project

**Basic Usage:**

```python
from repo2data.utils import locate_evidence_data

# Specify project name explicitly
data_path = locate_evidence_data("my_dataset")
# Returns: /absolute/path/to/repo/data/my_dataset/

# Load your data
import pandas as pd
df = pd.read_csv(data_path / "results.csv")
```

**Auto-detect project name from config:**

If your `myst.yml` has `data.projectName` field:

```python
# No need to specify project name!
data_path = locate_evidence_data()
```

**Advanced options:**

```python
# Start search from specific directory
data_path = locate_evidence_data(
    project_name="my_dataset",
    start_dir="/path/to/start"
)

# Look for specific config files
data_path = locate_evidence_data(
    project_name="my_dataset",
    config_files=["custom_config.yml", "myst.yml"]
)

# Don't verify existence (useful when creating new datasets)
data_path = locate_evidence_data(
    project_name="new_dataset",
    verify_exists=False
)
data_path.mkdir(parents=True, exist_ok=True)
```

**Common use case - Jupyter notebook:**

```python
# In notebook at: repo/content/analysis/experiment1/analysis.ipynb
from repo2data.utils import locate_evidence_data
import pandas as pd
import matplotlib.pyplot as plt

# Automatically finds repo/data/my_dataset/ regardless of notebook location
data_path = locate_evidence_data("my_dataset")

# Load and analyze
df = pd.read_csv(data_path / "experiment_results.csv")
plt.plot(df['time'], df['value'])
plt.savefig(data_path / "plot.png")
```

### `list_evidence_datasets()` - See All Available Datasets

List all datasets in your repository's data directory:

```python
from repo2data.utils import list_evidence_datasets

# Get list of all available datasets
datasets = list_evidence_datasets()
print(datasets)
# Output: ['dataset1', 'dataset2', 'my_analysis_data']

# Use with locate_evidence_data
for dataset in datasets:
    path = locate_evidence_data(dataset)
    print(f"{dataset}: {path}")
```

**Advanced usage:**

```python
# Start from specific directory
datasets = list_evidence_datasets(start_dir="/path/to/repo")

# Use custom config files
datasets = list_evidence_datasets(
    config_files=["custom_config.yml"]
)
```

## Global Cache System

Repo2Data uses an intelligent global cache system to avoid re-downloading data.

### Cache Location

Cache database is stored at: `~/.cache/repo2data/cache.db` (Linux/macOS) or `%LOCALAPPDATA%\repo2data\cache` (Windows)

### How Caching Works

1. **Content-based caching**: Cache key is computed from `src`, `projectName`, and `version`
2. **Automatic validation**: Checks if cached data still exists on disk
3. **Metadata tracking**: Stores size, file count, timestamps
4. **Auto-migration**: Old local caches are automatically migrated to global cache

### Cache CLI Commands

Repo2Data provides powerful CLI commands to manage your cache:

#### View All Cached Datasets

```bash
repo2data cache list
```

Shows table with:
- Cache key
- Project name
- Destination path
- Size
- File count
- Last accessed time

Sort by different fields:

```bash
repo2data cache list --sort-by size        # Sort by size
repo2data cache list --sort-by accessed    # Sort by last access
repo2data cache list --sort-by project     # Sort by project name (default)
```

Filter by project:

```bash
repo2data cache list --filter my_dataset
```

#### Show Cache Statistics

```bash
repo2data cache info
```

Displays:
- Total number of cached datasets
- Total size of cached data
- Cache database location
- Oldest and newest cache entries

#### Verify Cache Integrity

Check if cached data still exists on disk:

```bash
repo2data cache verify
```

Shows which cache entries are still valid vs. orphaned (data deleted from disk).

#### Clean Orphaned Entries

Remove cache entries where data no longer exists:

```bash
repo2data cache clean
```

Use `--dry-run` to preview what will be removed:

```bash
repo2data cache clean --dry-run
```

#### Remove Specific Cache Entry

Remove by project name:

```bash
repo2data cache remove my_dataset
```

Remove by destination path:

```bash
repo2data cache remove /path/to/data --path
```

#### Clear All Cache

Remove all cache entries (does NOT delete actual data):

```bash
repo2data cache clear
```

Confirm with `--yes` to skip prompt:

```bash
repo2data cache clear --yes
```

#### Migrate Local Caches

If you have old local cache files (`repo2data_cache.json`), migrate them to global cache:

```bash
# Migrate caches in current directory and subdirectories
repo2data cache migrate

# Migrate from specific paths
repo2data cache migrate /path/to/project1 /path/to/project2

# Remove local cache files after migration
repo2data cache migrate --remove
```

**Note:** Local caches are automatically migrated when accessed, so manual migration is usually not needed.

### Disable Global Cache

If you prefer local caching:

```bash
export REPO2DATA_USE_LOCAL_CACHE=1
```

## Download Features

### Progress Tracking

All downloads show detailed progress bars with:
- File name
- Progress percentage
- Downloaded size / Total size
- Transfer speed (MB/s)
- Estimated time remaining

Progress bars persist after completion so you can see final statistics.

### Checksum Verification

Ensure data integrity with automatic checksum verification:

```yaml
data:
  src: "https://example.com/data.zip"
  dst: "./data"
  projectName: "verified_data"
  checksum: "a7b3c4d5e6f7..."
  checksum_algorithm: "sha256"
```

Generate checksums:

```bash
# Linux/macOS
sha256sum filename

# Windows
certutil -hashfile filename SHA256

# Python
from repo2data.utils import compute_checksum
hash_value = compute_checksum("path/to/file", "sha256")
```

### Disk Space Checking

Repo2Data automatically:
- Checks available disk space before downloading
- Requires 100MB buffer in addition to file size
- Raises clear error if insufficient space

### Automatic Decompression

Archives are automatically extracted:
- Supported formats: `.zip`, `.tar`, `.tar.gz`, `.tgz`, `.tar.bz2`, `.rar`, and more
- Archives are deleted after successful extraction
- macOS junk files (`.DS_Store`, `__MACOSX/`, `._*`) are automatically removed

### Atomic Downloads

Downloads are atomic and safe:
- Files download to `.tmp` extension first
- Renamed to final name only on success
- Failed downloads are automatically cleaned up

## Multiple Datasets

Download multiple datasets in one configuration:

```yaml
data:
  experiment1:
    src: "doi:10.5281/zenodo.1234567"
    dst: "./data"
    projectName: "experiment1_data"

  experiment2:
    src: "https://figshare.com/articles/dataset/Title/98765"
    dst: "./data"
    projectName: "experiment2_data"
```

## Supported Providers

Repo2Data supports multiple data repositories. Each provider has its own documentation page:

- **[Datalad](./datalad.md)** - Git-annex repositories
- **[Figshare](./figshare.md)** - Academic datasets with DOI
- **[Google Drive](./gdrive.md)** - Shared files and folders
- **[OSF](./osf.md)** - Open Science Framework projects
- **[Zenodo](./zenodo.md)** - Research datasets with DOI
- **[Dataverse](./dataverse.md)** - Dataverse repository network
- **HTTP/HTTPS** - Generic file downloads

The appropriate provider is automatically selected based on your `src` URL format.

## Best Practices

1. **Use version field**: Always specify `version` for reproducible research
   ```yaml
   version: "v1.0"  # or use date: "2024-01-15"
   ```

2. **Add checksums for critical data**: Verify data integrity
   ```yaml
   checksum: "hash_value_here"
   checksum_algorithm: "sha256"
   ```

3. **Use descriptive project names**: Makes data organization clear
   ```yaml
   projectName: "fmri_experiment_2024"  # Good
   projectName: "data1"  # Avoid
   ```

4. **Leverage locate utilities**: Use `locate_evidence_data()` in notebooks for portable code

5. **Clean up old caches**: Periodically run `repo2data cache verify` and `repo2data cache clean`

6. **Keep config at repo root**: Follow evidence/neurolibre convention with `myst.yml` at root

## Troubleshooting

### Data not found when using locate_evidence_data

**Problem**: `FileNotFoundError: Could not find config file`

**Solution**: Make sure you have a config file (`myst.yml`, `data_requirement.yaml`, etc.) at your repository root. The function searches upward from current directory.

### Download keeps happening despite cache

**Problem**: Data re-downloads every time

**Solution**:
- Check if `version` field changed in config (changing version triggers re-download)
- Verify cache with: `repo2data cache list`
- Check if data was deleted from destination directory

### Checksum verification fails

**Problem**: `ValueError: Checksum mismatch`

**Solution**:
- Verify the checksum value is correct
- Ensure you're using the right algorithm (sha256, md5, sha1)
- Data may be corrupted - try re-downloading
- For provider downloads (Zenodo, Figshare), ensure DOI/URL is correct

### Insufficient disk space error

**Problem**: `OSError: Insufficient disk space`

**Solution**:
- Free up disk space (at least file_size + 100MB needed)
- Change `dst` to a location with more space
- Check actual available space: `df -h` (Linux/macOS) or `dir` (Windows)

## Getting Help

- **Documentation**: Browse provider-specific guides in this docs folder
- **Examples**: Check `examples/` directory for sample configurations
- **Issues**: Report bugs at [GitHub Issues](https://github.com/SIMEXP/Repo2Data/issues)
- **Cache debugging**: Use `repo2data cache verify` and `repo2data cache info`

## Next Steps

Now that you understand the basics, explore provider-specific documentation:

- [Datalad Provider](./datalad.md)
- [Figshare Provider](./figshare.md)
- [Google Drive Provider](./gdrive.md)
- [OSF Provider](./osf.md)
- [Zenodo Provider](./zenodo.md)
- [Dataverse Provider](./dataverse.md)

Each guide includes detailed examples and provider-specific features!
