# Zenodo Provider

The Zenodo provider enables downloading of research datasets from [Zenodo](https://zenodo.org/), a general-purpose open-access repository hosted by CERN for research data, software, and publications.

## What is Zenodo?

Zenodo is a free, open-access repository where researchers can deposit:
- Research data
- Software and code
- Publications and reports
- Presentations and posters
- Images and media

All uploads receive a Digital Object Identifier (DOI) for permanent citation. Zenodo is integrated with GitHub and supports versioning, making it ideal for research reproducibility.

## Installation

### Install Repo2Data

```bash
pip install repo2data
```

### Install zenodo-get

The Zenodo provider requires `zenodo_get`:

```bash
pip install zenodo-get
```

## How It Works

The Zenodo provider:

1. **Detects Zenodo DOIs** with pattern `10.5281/zenodo.*`
2. **Uses `zenodo_get`** to download all files from the record
3. **Downloads to destination** with progress tracking
4. **Supports versioned records** for reproducibility

## Supported DOI Formats

Zenodo DOIs follow the pattern:

```
10.5281/zenodo.XXXXXXX
```

Where `XXXXXXX` is the numeric record ID.

### Valid Formats

```yaml
# Full DOI
src: "10.5281/zenodo.6482995"

# With doi: prefix
src: "doi:10.5281/zenodo.6482995"

# DOI URL
src: "https://doi.org/10.5281/zenodo.6482995"

# Zenodo URL
src: "https://zenodo.org/record/6482995"
```

All formats work - the provider extracts the DOI automatically.

## Configuration

### Basic Configuration

```yaml
data:
  src: "10.5281/zenodo.6482995"
  dst: "./data"
  projectName: "zenodo_dataset"
```

### Required Fields

- **`src`**: Zenodo DOI or URL
- **`dst`**: Destination directory for downloaded files
- **`projectName`**: Name for the dataset

### Optional Fields

- **`version`**: Version identifier for cache validation

## Examples

### Example 1: Download Using DOI

The most common and recommended method:

```yaml
data:
  src: "10.5281/zenodo.6482995"
  dst: "./data"
  projectName: "research_dataset"
```

**Command line:**

```bash
repo2data myst.yml
```

### Example 2: Download Using Full DOI

```yaml
data:
  src: "doi:10.5281/zenodo.6482995"
  dst: "./data"
  projectName: "research_dataset"
```

### Example 3: Download Using Zenodo URL

```yaml
data:
  src: "https://zenodo.org/record/6482995"
  dst: "./data"
  projectName: "research_dataset"
```

### Example 4: Multiple Zenodo Datasets

Download several datasets in one configuration:

```yaml
data:
  dataset1:
    src: "10.5281/zenodo.6482995"
    dst: "./data"
    projectName: "imaging_data"
    version: "v1.0"

  dataset2:
    src: "10.5281/zenodo.7123456"
    dst: "./data"
    projectName: "behavioral_data"
    version: "v2.1"

  supplementary:
    src: "10.5281/zenodo.8987654"
    dst: "./data"
    projectName: "supplementary_materials"
```

### Example 5: Using from Jupyter Notebook

```python
from repo2data import Repo2Data
from repo2data.utils import locate_evidence_data
import pandas as pd
import numpy as np

# Download data (skip if already cached)
r2d = Repo2Data("myst.yml")
r2d.install()

# Locate the downloaded data
data_path = locate_evidence_data("research_dataset")

# List all downloaded files
print("Downloaded files:")
for file in data_path.iterdir():
    if file.is_file():
        print(f"  - {file.name}")

# Load and analyze
csv_file = data_path / "results.csv"
df = pd.read_csv(csv_file)
print(f"\nLoaded {len(df)} rows of data")
```

### Example 6: Automated Workflow

```python
# In notebook: repo/content/analysis/statistical_analysis.ipynb
from repo2data.utils import locate_evidence_data
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd

# Automatically find data (works from any notebook location)
data_path = locate_evidence_data("research_dataset")

# Load data
df = pd.read_csv(data_path / "experimental_results.csv")

# Analyze
sns.boxplot(data=df, x="condition", y="response_time")
plt.savefig("figures/response_times.png")
print(f"Analyzed {len(df)} trials")
```

### Example 7: Versioned Dataset

Use specific Zenodo version for reproducibility:

```yaml
data:
  src: "10.5281/zenodo.6482995"  # Specific version DOI
  dst: "./data"
  projectName: "dataset_v1"
  version: "v1.0.0"  # Local version tag
```

Zenodo provides version-specific DOIs - always use the specific version DOI for reproducibility!

## Finding Zenodo Datasets

### Search Zenodo

1. Visit [zenodo.org](https://zenodo.org/)
2. Search for datasets in your field
3. Click on a record to view details
4. Copy the DOI from the right sidebar

### Get DOI from Record Page

On any Zenodo record page, find the DOI:

```
DOI: 10.5281/zenodo.6482995
```

Use this directly in your configuration.

### Understanding Zenodo Versions

Zenodo supports versioning:
- **Concept DOI**: `10.5281/zenodo.6482994` (always latest version)
- **Version DOI**: `10.5281/zenodo.6482995` (specific version)

**Best practice**: Use version-specific DOI for reproducibility!

## Download Behavior

### All Files Downloaded

`zenodo_get` downloads **all files** from a Zenodo record:
- Data files
- Documentation
- Code
- Supplementary materials

### File Organization

Files are saved to:
```
{dst}/{projectName}/
  ├── data.csv
  ├── metadata.json
  ├── README.md
  └── analysis_code.py
```

### Progress Display

`zenodo_get` shows:
- List of files to download
- Progress for each file
- Total size and download status

## Common Use Cases

### 1. Published Research Data

Download data accompanying published papers:

```yaml
data:
  src: "10.5281/zenodo.6482995"
  dst: "./data"
  projectName: "smith2023_data"
```

Many journals require data deposition on Zenodo.

### 2. Software Releases

Download specific software versions:

```yaml
data:
  src: "10.5281/zenodo.7891234"
  dst: "./data"
  projectName: "analysis_toolbox_v2"
```

### 3. GitHub Archive

Download archived GitHub releases (Zenodo-GitHub integration):

```yaml
data:
  src: "10.5281/zenodo.5567890"
  dst: "./data"
  projectName: "github_release_v1.0"
```

### 4. Reproducible Research

Pin exact data version for reproducibility:

```yaml
data:
  src: "10.5281/zenodo.6482995"  # Version-specific DOI
  dst: "./data"
  projectName: "reproducible_analysis"
  version: "paper_submission_v1"
```

### 5. Training Data

Download machine learning datasets:

```yaml
data:
  src: "10.5281/zenodo.3456789"
  dst: "./data"
  projectName: "ml_training_data"
```

## Advantages of Zenodo Provider

1. **Permanent DOIs**: Stable, citable identifiers
2. **Versioning**: Track dataset versions with separate DOIs
3. **Open Access**: Free for all users
4. **Large Storage**: Up to 50GB per dataset
5. **CERN Infrastructure**: Reliable, long-term preservation
6. **GitHub Integration**: Automatic archiving of GitHub releases
7. **Rich Metadata**: Comprehensive dataset descriptions

## Troubleshooting

### zenodo_get Not Installed

**Error**: `FileNotFoundError: zenodo_get is not installed`

**Solution**: Install zenodo-get:

```bash
pip install zenodo-get
```

### Invalid DOI

**Error**: `zenodo_get failed` - DOI not found

**Solution**:
- Verify DOI is correct
- Check if record is public (private records need authentication)
- Ensure DOI follows pattern `10.5281/zenodo.XXXXXXX`
- Copy DOI directly from Zenodo page

### Download Timeout

**Error**: Download hangs or times out

**Solution**:
- Check internet connection
- Large datasets may take time
- `zenodo_get` resumes interrupted downloads
- Retry - Repo2Data will use cache if available

### Insufficient Disk Space

**Error**: `OSError: Insufficient disk space`

**Solution**:
- Check dataset size on Zenodo page
- Free up disk space (need size + 100MB buffer)
- Change `dst` to location with more space

### MD5 Checksum Failed

**Error**: MD5 checksum mismatch

**Solution**:
- Delete partially downloaded files
- Retry download
- `zenodo_get` automatically verifies checksums
- Contact Zenodo support if persistent

## Best Practices

1. **Use version-specific DOIs** for reproducibility:
   ```yaml
   src: "10.5281/zenodo.6482995"  # Specific version
   # Not: 10.5281/zenodo.6482994  # Concept DOI (latest)
   ```

2. **Document the source** in your publication:
   ```
   Data available at: https://doi.org/10.5281/zenodo.6482995
   ```

3. **Add version tags** for local organization:
   ```yaml
   version: "v1.0.0"
   ```

4. **Cite properly**:
   - Include full Zenodo citation from record page
   - Use version-specific DOI in references
   - Credit dataset authors

5. **Check license** before use:
   - Review license on Zenodo record page
   - Ensure compliance with usage terms
   - Cite according to license requirements

## Zenodo-GitHub Integration

Zenodo can automatically archive GitHub releases:

1. Connect GitHub repository to Zenodo
2. Create GitHub release
3. Zenodo automatically creates archive and assigns DOI
4. Download via Repo2Data using the DOI

This provides permanent snapshots of code at specific versions.

## Authentication for Private Records

For embargoed or private Zenodo records:

```bash
# Get access token from Zenodo account settings
export ZENODO_TOKEN="your_access_token"

# Then use Repo2Data normally
repo2data myst.yml
```

## Zenodo Sandbox

For testing, Zenodo provides a sandbox:

```yaml
src: "10.5072/zenodo.123456"  # Sandbox DOI pattern
```

Note: Use production Zenodo (10.5281) for actual research.

## Related Resources

- [Zenodo Homepage](https://zenodo.org/)
- [Zenodo Help](https://help.zenodo.org/)
- [zenodo_get Documentation](https://github.com/dvolgyes/zenodo_get)
- [Zenodo API](https://developers.zenodo.org/)
- [GitHub-Zenodo Integration](https://docs.github.com/en/repositories/archiving-a-github-repository/referencing-and-citing-content)

## Comparison: Zenodo vs Other Repositories

**Zenodo advantages:**
- General purpose (any field)
- Large file support (50GB)
- GitHub integration
- CERN infrastructure

**Consider alternatives:**
- **Figshare**: Better for figures and presentations
- **Dataverse**: Better for domain-specific repositories
- **OSF**: Better for project management
- **Field-specific**: Like OpenNeuro for neuroimaging

## Back to Main Guide

Return to the [main documentation](./data.md) for general Repo2Data features and other providers.
