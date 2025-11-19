# Figshare Provider

The Figshare provider enables downloading of datasets from [Figshare](https://figshare.com/), a popular repository for sharing research outputs including datasets, figures, and supplementary materials.

## What is Figshare?

Figshare is a repository where researchers can preserve and share their research outputs, including datasets, figures, videos, and posters. Each item receives a DOI (Digital Object Identifier) for permanent citation and discovery.

## Installation

```bash
pip install repo2data
```

No additional dependencies required - the Figshare provider uses the official Figshare API.

## How It Works

The Figshare provider:

1. **Extracts article ID** from DOI, URL, or protocol identifier
2. **Fetches metadata** using Figshare API v2
3. **Downloads all files** associated with the article
4. **Shows progress bars** for each file download
5. **Verifies checksums** if provided

## Supported URL Formats

The Figshare provider recognizes multiple formats:

### 1. Figshare DOI

```yaml
src: "doi:10.6084/m9.figshare.7778845"
```

Standard Figshare DOI format (most common)

### 2. Full Figshare URL

```yaml
src: "https://figshare.com/articles/dataset/Example_Dataset/7778845"
```

Direct link to Figshare article page

### 3. Figshare Protocol

```yaml
src: "figshare://7778845"
```

Short form using article ID

### 4. DOI URL

```yaml
src: "https://doi.org/10.6084/m9.figshare.7778845"
```

Official DOI resolver URL

## Configuration

### Basic Configuration

```yaml
data:
  src: "doi:10.6084/m9.figshare.7778845"
  dst: "./data"
  projectName: "figshare_dataset"
```

### Required Fields

- **`src`**: Figshare identifier (DOI, URL, or protocol)
- **`dst`**: Destination directory for downloaded files
- **`projectName`**: Name for the dataset

### Optional Fields

- **`version`**: Version identifier for cache validation
- **`checksum`**: Expected checksum for verification (not commonly used for Figshare)

## Examples

### Example 1: Download Using DOI

The most common and recommended method:

```yaml
data:
  src: "doi:10.6084/m9.figshare.7778845"
  dst: "./data"
  projectName: "imaging_analysis_data"
  version: "v1.0"
```

**Command line:**

```bash
repo2data myst.yml
```

**Output:**
```
Figshare: Example Imaging Dataset
Files: 3
(1/3) data_file1.csv
  Downloading data_file1.csv ━━━━━━━━━━━━━━━ 100% 2.5 MB 5.2 MB/s 0:00:00
  ✓ Downloaded data_file1.csv
(2/3) data_file2.npy
  Downloading data_file2.npy ━━━━━━━━━━━━━━━ 100% 15.3 MB 8.1 MB/s 0:00:02
  ✓ Downloaded data_file2.npy
```

### Example 2: Download Using URL

```yaml
data:
  src: "https://figshare.com/articles/dataset/Brain_Connectivity_Data/12345678"
  dst: "./data"
  projectName: "connectivity_study"
```

### Example 3: Download Using Protocol

```yaml
data:
  src: "figshare://12345678"
  dst: "./data"
  projectName: "figshare_study"
```

### Example 4: Multiple Figshare Datasets

Download several datasets in one configuration:

```yaml
data:
  study1:
    src: "doi:10.6084/m9.figshare.7778845"
    dst: "./data"
    projectName: "study1_data"

  study2:
    src: "doi:10.6084/m9.figshare.9876543"
    dst: "./data"
    projectName: "study2_data"

  supplementary:
    src: "https://figshare.com/articles/dataset/Supplementary/11111111"
    dst: "./data"
    projectName: "supplementary_materials"
```

### Example 5: Using in Jupyter Notebook

```python
from repo2data import Repo2Data
from repo2data.utils import locate_evidence_data
import pandas as pd
import numpy as np

# Download data (only runs if not already cached)
r2d = Repo2Data("myst.yml")
r2d.install()

# Locate the downloaded data
data_path = locate_evidence_data("imaging_analysis_data")

# Load and analyze
csv_file = data_path / "data_file1.csv"
df = pd.read_csv(csv_file)

npy_file = data_path / "data_file2.npy"
array = np.load(npy_file)

print(f"CSV shape: {df.shape}")
print(f"Array shape: {array.shape}")
```

### Example 6: Automatic Cache Detection

```python
# In notebook at: repo/content/notebooks/analysis.ipynb
from repo2data.utils import locate_evidence_data
import matplotlib.pyplot as plt
import pandas as pd

# Automatically finds data (no re-download if cached)
data_path = locate_evidence_data("imaging_analysis_data")

# Your analysis code
df = pd.read_csv(data_path / "timeseries.csv")
plt.plot(df['time'], df['signal'])
plt.savefig("figures/timeseries.png")
```

## Finding Figshare Datasets

### Search Figshare

1. Visit [figshare.com](https://figshare.com/)
2. Search for datasets in your field
3. Click on a dataset to view details
4. Copy the DOI or URL

### Get DOI from Article Page

On any Figshare article page, find the DOI in the citation section:

```
DOI: 10.6084/m9.figshare.7778845
```

Use this directly in your configuration:

```yaml
src: "doi:10.6084/m9.figshare.7778845"
```

### Extract Article ID from URL

From URL: `https://figshare.com/articles/dataset/Title/7778845`

Article ID: `7778845`

Use as: `figshare://7778845`

## Download Behavior

### All Files Downloaded

The Figshare provider downloads **all files** associated with an article:

- Dataset files
- Supplementary materials
- Figures
- Documentation

### File Organization

Files are saved to:
```
{dst}/{projectName}/
  ├── file1.csv
  ├── file2.npy
  ├── readme.txt
  └── figure1.png
```

### Progress Tracking

Each file shows individual progress:
- File name
- Download progress bar
- Size downloaded / Total size
- Transfer speed
- Estimated time remaining

## Metadata Access

Figshare provides rich metadata through its API:

```python
from repo2data.providers.figshare import FigshareProvider
from pathlib import Path

# Create provider
config = {
    "src": "doi:10.6084/m9.figshare.7778845",
    "projectName": "test"
}
provider = FigshareProvider(config, Path("./data/test"))

# Fetch metadata
article_id = provider._extract_article_id(config["src"])
metadata = provider._get_article_metadata(article_id)

# Access metadata
print(f"Title: {metadata['title']}")
print(f"Authors: {[a['full_name'] for a in metadata['authors']]}")
print(f"Published: {metadata['published_date']}")
print(f"Files: {len(metadata['files'])}")
```

## Common Use Cases

### 1. Published Research Data

Download supplementary data from published papers:

```yaml
data:
  src: "doi:10.6084/m9.figshare.7778845"
  dst: "./data"
  projectName: "paper_supplementary_data"
```

### 2. Sharing Lab Data

Access datasets shared by other research groups:

```yaml
data:
  src: "https://figshare.com/articles/dataset/Lab_Dataset/12345678"
  dst: "./data"
  projectName: "external_lab_data"
```

### 3. Figures and Visualizations

Download figures for meta-analysis:

```yaml
data:
  src: "figshare://98765432"
  dst: "./data"
  projectName: "meta_analysis_figures"
```

### 4. Reproducible Research

Pin specific versions for reproducibility:

```yaml
data:
  src: "doi:10.6084/m9.figshare.7778845"
  dst: "./data"
  projectName: "reproducible_analysis"
  version: "v1"  # Cache key - changing this triggers re-download
```

## Advantages of Figshare Provider

1. **Automatic API Integration**: No manual download needed
2. **Rich Metadata**: Access article information programmatically
3. **Progress Tracking**: Visual feedback for large files
4. **Persistent DOIs**: Permanent links to datasets
5. **Multi-file Support**: Downloads all associated files automatically

## Troubleshooting

### Article Not Found

**Error**: `Failed to fetch Figshare article metadata`

**Solution**:
- Verify the article ID or DOI is correct
- Check if article is public (private articles require authentication)
- Ensure you have internet connection

### Invalid DOI Format

**Error**: `Could not extract Figshare article ID`

**Solution**:
- Figshare DOIs follow pattern: `10.6084/m9.figshare.XXXXXXX`
- Use DOI exactly as shown on Figshare page
- Try using the direct URL instead

### Download Timeout

**Error**: Connection timeout during download

**Solution**:
- Check internet connection
- Large files may take time - wait for completion
- Repo2Data retries automatically on network errors

### Insufficient Disk Space

**Error**: `OSError: Insufficient disk space`

**Solution**:
- Check available disk space
- Free up space (need file size + 100MB buffer)
- Change `dst` to location with more space

## Best Practices

1. **Use DOI format** for clarity and permanence:
   ```yaml
   src: "doi:10.6084/m9.figshare.7778845"  # Preferred
   ```

2. **Add version tags** for reproducibility:
   ```yaml
   version: "v1.0"
   ```

3. **Document the source** in your README or paper:
   ```
   Data downloaded from: https://doi.org/10.6084/m9.figshare.7778845
   ```

4. **Cite properly**: Include Figshare DOI in your citations

5. **Leverage caching**: Repo2Data avoids re-downloads automatically

## Figshare API

The Figshare provider uses API v2:
- Endpoint: `https://api.figshare.com/v2`
- No authentication required for public articles
- Rate limits: Generous for normal use

For private articles, see Figshare API documentation for authentication.

## Related Resources

- [Figshare Homepage](https://figshare.com/)
- [Figshare API Documentation](https://docs.figshare.com/)
- [Finding Figshare DOIs](https://help.figshare.com/article/how-to-cite-figshare-content)

## Back to Main Guide

Return to the [main documentation](./data.md) for general Repo2Data features and other providers.
