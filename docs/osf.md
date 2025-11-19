# OSF Provider

The OSF provider enables downloading of research materials from the [Open Science Framework (OSF)](https://osf.io/), a free platform for sharing research data, code, and materials.

## What is OSF?

The Open Science Framework (OSF) is a free, open-source platform built to support research workflow, including:
- Data storage and sharing
- Collaboration
- Project management
- Preprint hosting
- Pre-registration
- Version control

OSF is widely used in psychology, neuroscience, and other research fields for open science practices.

## Installation

### Install Repo2Data

```bash
pip install repo2data
```

### Install osfclient

The OSF provider requires `osfclient`:

```bash
pip install osfclient
```

## How It Works

The OSF provider:

1. **Detects OSF URLs** containing `osf.io`
2. **Extracts project ID** from the URL
3. **Uses `osfclient`** to download files
4. **Supports selective downloads** via `remote_filepath` parameter
5. **Clones entire projects** or downloads specific files

## Supported URL Formats

OSF project URLs follow this pattern:

```
https://osf.io/XXXXX/
```

Where `XXXXX` is a 5-character project ID.

**Examples:**
- `https://osf.io/abc12/`
- `https://osf.io/xyz98/files/`
- `https://osf.io/def45/wiki/`

## Configuration

### Basic Configuration - Download Entire Project

```yaml
data:
  src: "https://osf.io/abc12/"
  dst: "./data"
  projectName: "osf_project"
```

### Download Specific Files

```yaml
data:
  src: "https://osf.io/abc12/"
  dst: "./data"
  projectName: "osf_project"
  remote_filepath: "data/experiment1.csv"
```

### Download Multiple Specific Files

```yaml
data:
  src: "https://osf.io/abc12/"
  dst: "./data"
  projectName: "osf_project"
  remote_filepath:
    - "data/experiment1.csv"
    - "data/experiment2.csv"
    - "analysis/results.json"
```

### Required Fields

- **`src`**: OSF project URL
- **`dst`**: Destination directory
- **`projectName`**: Name for the dataset

### Optional Fields

- **`remote_filepath`**: String or list of specific file paths to download
- **`version`**: Version identifier for cache management

## Examples

### Example 1: Download Entire Project

```yaml
data:
  src: "https://osf.io/abc12/"
  dst: "./data"
  projectName: "psychology_study"
```

**Command line:**

```bash
repo2data myst.yml
```

This downloads all files from the OSF project to `./data/psychology_study/`

### Example 2: Download Specific File

```yaml
data:
  src: "https://osf.io/xyz98/"
  dst: "./data"
  projectName: "fmri_data"
  remote_filepath: "raw_data/subject01_bold.nii.gz"
```

Only downloads the specified file, preserving directory structure.

### Example 3: Download Multiple Files

```yaml
data:
  src: "https://osf.io/def45/"
  dst: "./data"
  projectName: "behavioral_experiment"
  remote_filepath:
    - "data/participant_responses.csv"
    - "data/stimulus_timing.json"
    - "analysis/preprocessing.py"
    - "results/figures/figure1.png"
```

Downloads only the listed files.

### Example 4: Multiple OSF Projects

```yaml
data:
  study1:
    src: "https://osf.io/abc12/"
    dst: "./data"
    projectName: "study1_data"
    remote_filepath: "data/results.csv"

  study2:
    src: "https://osf.io/xyz98/"
    dst: "./data"
    projectName: "study2_data"

  supplementary:
    src: "https://osf.io/def45/"
    dst: "./data"
    projectName: "supplementary_materials"
    remote_filepath:
      - "figures/figure1.pdf"
      - "tables/table1.csv"
```

### Example 5: Using from Jupyter Notebook

```python
from repo2data import Repo2Data
from repo2data.utils import locate_evidence_data
import pandas as pd
import json

# Download data (skip if cached)
r2d = Repo2Data("myst.yml")
r2d.install()

# Locate the downloaded data
data_path = locate_evidence_data("behavioral_experiment")

# Load data
responses = pd.read_csv(data_path / "data" / "participant_responses.csv")
with open(data_path / "data" / "stimulus_timing.json") as f:
    timing = json.load(f)

print(f"Loaded {len(responses)} responses")
print(f"Timing events: {len(timing)}")
```

### Example 6: Preprocessing Pipeline

```python
# In notebook: repo/content/notebooks/preprocessing.ipynb
from repo2data.utils import locate_evidence_data
from pathlib import Path
import pandas as pd

# Automatically find data (works from any directory depth)
raw_data_path = locate_evidence_data("psychology_study")

# Process all CSV files
csv_files = raw_data_path.rglob("*.csv")
for csv_file in csv_files:
    df = pd.read_csv(csv_file)
    # Your preprocessing
    print(f"Processed {csv_file.name}: {len(df)} rows")
```

## Finding OSF Projects

### Browse OSF

1. Visit [osf.io](https://osf.io/)
2. Search for projects in your field
3. Click on a project to view details
4. Copy the project URL from the address bar

### Project URL Structure

Project URL: `https://osf.io/abc12/`

Project ID: `abc12` (always 5 characters)

### Finding File Paths

To specify `remote_filepath`:

1. Navigate to the project on OSF
2. Click "Files" tab
3. Browse to the file you want
4. Note the path structure
5. Use the path relative to project root

**Example:**
- OSF shows: `OSF Storage/data/experiment1.csv`
- Use as: `remote_filepath: "data/experiment1.csv"`

## Download Behavior

### Entire Project Clone

Without `remote_filepath`, the provider clones the entire project:

```
{dst}/{projectName}/
  ├── data/
  │   ├── file1.csv
  │   └── file2.npy
  ├── analysis/
  │   └── script.py
  └── README.md
```

### Selective Download

With `remote_filepath`, only specified files are downloaded:

```
{dst}/{projectName}/
  └── data/
      └── experiment1.csv
```

Directory structure is preserved.

### Progress Display

`osfclient` shows download progress for files.

## Common Use Cases

### 1. Published Research Data

Download data from published papers:

```yaml
data:
  src: "https://osf.io/abc12/"
  dst: "./data"
  projectName: "smith2023_replication"
```

### 2. Pre-registered Studies

Access pre-registration materials:

```yaml
data:
  src: "https://osf.io/xyz98/"
  dst: "./data"
  projectName: "preregistration_materials"
  remote_filepath:
    - "preregistration.pdf"
    - "analysis_plan.Rmd"
```

### 3. Supplementary Materials

Download specific supplementary files:

```yaml
data:
  src: "https://osf.io/def45/"
  dst: "./data"
  projectName: "paper_supplements"
  remote_filepath:
    - "supplementary_table_1.csv"
    - "supplementary_figure_1.png"
```

### 4. Collaborative Projects

Access shared project data:

```yaml
data:
  src: "https://osf.io/collab/"
  dst: "./data"
  projectName: "team_collaboration"
```

### 5. Replication Studies

Download original data for replication:

```yaml
data:
  original_study:
    src: "https://osf.io/orig1/"
    dst: "./data"
    projectName: "original_study_data"

  replication_study:
    src: "https://osf.io/repl1/"
    dst: "./data"
    projectName: "replication_study_data"
```

## Advantages of OSF Provider

1. **Open Science**: Supports transparency and reproducibility
2. **Selective Downloads**: Download only needed files
3. **Version Control**: OSF tracks file versions
4. **Persistent Links**: OSF projects have stable URLs
5. **Rich Metadata**: Projects include descriptions, citations, contributors

## Troubleshooting

### osfclient Not Installed

**Error**: `FileNotFoundError: osfclient is not installed`

**Solution**: Install osfclient:

```bash
pip install osfclient
```

### Project ID Extraction Failed

**Error**: `ValueError: Cannot extract OSF project ID from URL`

**Solution**:
- Ensure URL follows format: `https://osf.io/XXXXX/`
- Project ID must be exactly 5 characters
- Copy URL directly from OSF address bar

### File Not Found

**Error**: OSF fetch failed for specific file

**Solution**:
- Verify file path is correct (case-sensitive)
- Check if file exists in the OSF project
- Navigate to Files tab on OSF to confirm path
- Path should be relative to project root
- OSF Storage prefix is not needed in path

### Permission Denied

**Error**: Access denied to OSF project

**Solution**:
- Ensure project is public
- Private projects require authentication
- Contact project owner for access
- Check if project URL is correct

### Download Failed

**Error**: `osf command failed with return code X`

**Solution**:
- Check internet connection
- Verify project ID is correct
- Ensure `osfclient` is up to date: `pip install --upgrade osfclient`
- Check OSF service status at [status.cos.io](https://status.cos.io/)

## Authentication for Private Projects

For private OSF projects, configure authentication:

```bash
# Set OSF credentials as environment variables
export OSF_USERNAME="your_email@example.com"
export OSF_PASSWORD="your_password"

# Or configure osfclient
osf config
```

Then use Repo2Data normally:

```bash
repo2data myst.yml
```

## Best Practices

1. **Use specific file paths** when possible to minimize downloads:
   ```yaml
   remote_filepath: ["data/file1.csv", "data/file2.csv"]
   ```

2. **Document the OSF project** in your README:
   ```markdown
   Data source: https://osf.io/abc12/
   Citation: [Project title]. OSF. doi:10.17605/OSF.IO/ABC12
   ```

3. **Add version for reproducibility**:
   ```yaml
   version: "2024-01-15"  # Date of OSF snapshot
   ```

4. **Cite OSF projects properly**:
   - Include OSF DOI if available
   - Credit project contributors
   - Follow citation format from OSF project page

5. **Check file sizes** before downloading entire project:
   - Large projects may take significant time/space
   - Use `remote_filepath` for selective download

## OSF DOIs

Some OSF projects have DOIs for citation:

```
https://doi.org/10.17605/OSF.IO/ABC12
```

Use the OSF URL (not DOI URL) in your configuration:

```yaml
src: "https://osf.io/abc12/"  # Use this
# Not: https://doi.org/10.17605/OSF.IO/ABC12
```

## Working with OSF Storage

OSF supports multiple storage providers:
- OSF Storage (default)
- GitHub
- Google Drive
- Dropbox
- Others

The OSF provider works with OSF Storage. For other integrations, use the appropriate provider (e.g., GitHub provider for GitHub-connected storage).

## Related Resources

- [OSF Homepage](https://osf.io/)
- [OSF Help](https://help.osf.io/)
- [osfclient Documentation](https://github.com/osfclient/osfclient)
- [Center for Open Science](https://www.cos.io/)

## Back to Main Guide

Return to the [main documentation](./data.md) for general Repo2Data features and other providers.
