[![CircleCI](https://circleci.com/gh/SIMEXP/Repo2Data.svg?style=svg)](https://circleci.com/gh/SIMEXP/Repo2Data) ![](https://img.shields.io/pypi/v/repo2data?style=flat&logo=python&logoColor=white&logoSize=8&labelColor=rgb(255%2C0%2C0)&color=white) [![Python 3.7+](https://img.shields.io/badge/python-3.7+-blue.svg)](https://www.python.org/downloads/release/python-370/) ![GitHub](https://img.shields.io/github/license/SIMEXP/repo2data)

# Repo2Data

Repo2Data is a **Python 3.7+** package that automatically fetches data from remote sources with intelligent caching and automatic decompression.

## ✨ New in Version 3.0

**Major refactoring with improved architecture:**
- 🎯 **Modular plugin-based architecture** - Easy to extend with new data sources
- 📝 **YAML support** - Use YAML configuration files in addition to JSON
- 🔒 **Enhanced security** - Better validation and deprecated unsafe features
- ⚡ **Sophisticated caching** - Content-based cache validation
- 📊 **Better logging** - Proper logging framework with configurable levels
- 📍 **Data locator** - Find datasets from notebooks without hardcoded paths
- 🔄 **Backwards compatible** - Existing code continues to work

## Supported Data Sources

- 🌐 **HTTP/HTTPS** - Any publicly accessible URL
- 📦 **AWS S3** - Amazon S3 buckets (via AWS CLI)
- 🔬 **Datalad** - Git-annex datasets
- 🎓 **Zenodo** - Academic datasets via DOI
- 🔓 **OSF** - Open Science Framework projects
- 💾 **Google Drive** - Public Google Drive files

## Installation

### Using pip

```bash
pip install repo2data
```

For Datalad support, you'll need [git-annex](https://git-annex.branchable.com/install/):

```bash
# Debian/Ubuntu
sudo apt-get install git-annex

# macOS
brew install git-annex
```

### Using Docker (Recommended)

The Docker image includes all dependencies:

```bash
git clone https://github.com/SIMEXP/Repo2Data
docker build --tag repo2data ./Repo2Data/
```

## Quick Start

### 1. Create a configuration file

**JSON format** (`data_requirement.json`):
```json
{
  "src": "https://github.com/SIMEXP/Repo2Data/archive/master.tar.gz",
  "dst": "./data",
  "projectName": "my_dataset"
}
```

**YAML format** (`data_requirement.yaml`):
```yaml
data:
  src: "https://github.com/SIMEXP/Repo2Data/archive/master.tar.gz"
  dst: "./data"
  projectName: "my_dataset"
```

### 2. Download the data

**Command line:**
```bash
# Uses data_requirement.json in current directory
repo2data

# Specify a different file
repo2data -r path/to/config.yaml

# Enable debug logging
repo2data -r config.yaml --log-level DEBUG
```

**Python API (New):**
```python
from repo2data import DatasetManager

# Initialize manager
manager = DatasetManager("data_requirement.yaml")

# Download datasets
paths = manager.install()
print(f"Data downloaded to: {paths}")
```

**Python API (Legacy - still works):**
```python
from repo2data import Repo2Data

repo2data = Repo2Data("data_requirement.json")
paths = repo2data.install()
```

## Configuration Reference

### Required Fields

- `src` - Source URL or command
- `projectName` - Name of the output directory

### Optional Fields

- `dst` - Destination directory (default: `./data`)
- `version` - Version string for cache invalidation
- `dataLayout` - Special layout handling (e.g., `"neurolibre"`)
- `remote_filepath` - Specific files to download (OSF only)

## Examples

### HTTP Archive Download

```json
{
  "src": "https://example.com/data.tar.gz",
  "dst": "./data",
  "projectName": "archive_data"
}
```

The archive will be automatically extracted and the `.tar.gz` file removed.

### Google Drive

Make your file **publicly accessible** and get the file ID from the URL:

```json
{
  "src": "https://drive.google.com/uc?id=YOUR_FILE_ID",
  "dst": "./data",
  "projectName": "gdrive_data"
}
```

### Datalad / Git-annex

```json
{
  "src": "https://github.com/OpenNeuroDatasets/ds000005.git",
  "dst": "./data",
  "projectName": "openneuro_dataset"
}
```

### AWS S3

```json
{
  "src": "s3://openneuro.org/ds000005",
  "dst": "./data",
  "projectName": "s3_dataset"
}
```

### Zenodo

Use the DOI from your Zenodo dataset:

```json
{
  "src": "10.5281/zenodo.6482995",
  "dst": "./data",
  "projectName": "zenodo_data"
}
```

### OSF (Open Science Framework)

**Download entire project:**
```json
{
  "src": "https://osf.io/fuqsk/",
  "dst": "./data",
  "projectName": "osf_project"
}
```

**Download specific files:**
```json
{
  "src": "https://osf.io/fuqsk/",
  "remote_filepath": ["file1.txt", "subfolder/file2.txt"],
  "dst": "./data",
  "projectName": "osf_files"
}
```

### Multiple Downloads

**JSON format:**
```json
{
  "dataset1": {
    "src": "https://example.com/data1.zip",
    "dst": "./data",
    "projectName": "data1"
  },
  "dataset2": {
    "src": "s3://bucket/data2",
    "dst": "./data",
    "projectName": "data2"
  }
}
```

**YAML format:**
```yaml
data:
  dataset1:
    src: "https://example.com/data1.zip"
    dst: "./data"
    projectName: "data1"

  dataset2:
    src: "s3://bucket/data2"
    dst: "./data"
    projectName: "data2"
```

## Advanced Usage

### Cache Management

Repo2Data uses intelligent caching - data is only re-downloaded if critical fields change:

```python
from repo2data import DatasetDownloader

downloader = DatasetDownloader(config)

# Check if cached
if downloader.is_cached():
    print("Data already downloaded!")
else:
    downloader.download()

# Force re-download
downloader.invalidate_cache()
downloader.download()
```

### Custom Logging

```python
from repo2data import setup_logger, DatasetManager
import logging

# Setup custom logging
setup_logger(
    level=logging.DEBUG,
    log_file="repo2data.log"
)

manager = DatasetManager("config.yaml")
manager.install()
```

### Programmatic Provider Selection

```python
from repo2data.providers import registry

# List available providers
providers = registry.list_providers()
print(f"Available: {providers}")

# Get provider for specific source
from pathlib import Path
provider = registry.get_provider(
    source="s3://bucket/data",
    config={"src": "s3://bucket/data", "projectName": "test"},
    destination=Path("./data")
)
print(f"Selected: {provider.provider_name}")
```

### Locating Data in Notebooks

When working with notebooks in nested directories (e.g., `content/notebooks/analysis.ipynb`), you can use `locate_evidence_data()` to find your datasets without hardcoding paths:

```python
from repo2data import locate_evidence_data

# Works from any nested directory in the repository
# Automatically finds <repo_root>/data/<project_name>
data_path = locate_evidence_data("my_dataset")

# Use the path to load your data
import pandas as pd
df = pd.read_csv(data_path / "results.csv")
```

**Auto-detect project name from config:**
```python
# Reads projectName from myst.yml or data_requirement.yaml
data_path = locate_evidence_data()
```

**List all available datasets:**
```python
from repo2data import list_evidence_datasets

datasets = list_evidence_datasets()
print(f"Available datasets: {datasets}")
```

**How it works:**
- Traverses upward from current directory to find `myst.yml` (or other config files)
- Constructs path following evidence/neurolibre convention: `<repo_root>/data/<project_name>`
- Works reliably from notebooks at any depth in your repository

**Benefits:**
- ✓ No hardcoded paths in notebooks
- ✓ Works from any nested directory
- ✓ Follows evidence/neurolibre conventions
- ✓ Simple one-line API

See [`examples/locator_usage.py`](examples/locator_usage.py) for more examples.

## Architecture

Repo2Data 3.0 features a modular architecture:

```
repo2data/
├── config/          # Configuration loading (JSON/YAML)
├── providers/       # Pluggable data source providers
│   ├── http.py      # HTTP/HTTPS downloads
│   ├── gdrive.py    # Google Drive
│   ├── s3.py        # AWS S3
│   ├── datalad.py   # Git-annex
│   ├── zenodo.py    # Zenodo DOI
│   └── osf.py       # OSF
├── cache/           # Intelligent caching system
├── utils/           # Logging, decompression, validation
├── manager.py       # Main orchestrator
└── downloader.py    # Download executor
```

## Security Notes

⚠️ **LibraryProvider Deprecated**: The Python library execution feature has been deprecated due to security concerns (arbitrary code execution). Use dedicated providers or install libraries separately.

## Migration from 2.x

Version 3.0 is fully backwards compatible. Old code continues to work with deprecation warnings:

**Old API (still works):**
```python
from repo2data.repo2data import Repo2Data
repo2data = Repo2Data("data_requirement.json")
```

**New API (recommended):**
```python
from repo2data import DatasetManager
manager = DatasetManager("data_requirement.json")
```

## CLI Reference

```bash
repo2data [OPTIONS]

Options:
  -r, --requirement PATH      Path to config file or GitHub URL
  --server                    Enable server mode (force destination)
  --destination DIR           Destination for server mode (default: ./data)
  -l, --log-level LEVEL       Logging level (DEBUG|INFO|WARNING|ERROR|CRITICAL)
  --log-file FILE             Write logs to file
  -v, --version               Show version
  -h, --help                  Show help message
```

## Examples

See the [`examples/`](examples/) directory for more examples in both JSON and YAML formats.

## Development

### Running Tests

```bash
pytest tests/
```

### Adding a New Provider

1. Create a new provider class inheriting from `BaseProvider`
2. Implement `can_handle()`, `download()`, and `provider_name`
3. Register it in `repo2data/downloader.py`

Example:
```python
from repo2data.providers.base import BaseProvider

class MyProvider(BaseProvider):
    def can_handle(self, source: str) -> bool:
        return source.startswith("myprovider://")

    def download(self) -> Path:
        # Download logic here
        return self.destination

    @property
    def provider_name(self) -> str:
        return "My Provider"
```

## Contributing

Contributions are welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Add tests for new features
4. Ensure all tests pass
5. Submit a pull request

## License

MIT License - see [LICENSE](LICENSE) file for details.

## Citation

If you use Repo2Data in your research, please cite:

```bibtex
@software{repo2data,
  title = {Repo2Data: Automated Data Fetching with Caching},
  author = {Tetrel, L. and Karakuzu, A.},
  url = {https://github.com/SIMEXP/Repo2Data},
  year = {2024}
}
```

## Support

- Documentation: [https://github.com/SIMEXP/Repo2Data](https://github.com/SIMEXP/Repo2Data)
- Issues: [https://github.com/SIMEXP/Repo2Data/issues](https://github.com/SIMEXP/Repo2Data/issues)
- Discussions: [https://github.com/SIMEXP/Repo2Data/discussions](https://github.com/SIMEXP/Repo2Data/discussions)
