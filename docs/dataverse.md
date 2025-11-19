# Dataverse Provider

The Dataverse provider enables downloading of datasets from [Dataverse](https://dataverse.org/) repositories worldwide, a network of research data repositories used across many institutions and disciplines.

## What is Dataverse?

Dataverse is open-source repository software for sharing, preserving, citing, exploring, and analyzing research data. Many universities and research institutions host their own Dataverse installations, creating a global network of interconnected data repositories.

Key features:
- **Persistent identifiers (DOIs)** for datasets
- **Versioning** for dataset updates
- **Metadata standards** for discovery
- **Access control** and embargoes
- **Citation tracking** for data reuse

## Installation

```bash
pip install repo2data
```

No additional dependencies required - the Dataverse provider uses the official Dataverse API.

## How It Works

The Dataverse provider:

1. **Detects Dataverse URLs or DOIs** containing Dataverse patterns
2. **Fetches dataset metadata** using Dataverse API
3. **Downloads all files** from the dataset
4. **Shows progress bars** for each file
5. **Supports multiple Dataverse installations** worldwide

## Supported Dataverse Installations

The provider recognizes these major Dataverse installations:

- **Harvard Dataverse**: [dataverse.harvard.edu](https://dataverse.harvard.edu)
- **DataverseNL**: [dataverse.nl](https://dataverse.nl)
- **AUSSDA**: [data.aussda.at](https://data.aussda.at)
- **DataverseNO**: [dataverse.no](https://dataverse.no)
- **UNC Dataverse**: [dataverse.unc.edu](https://dataverse.unc.edu)
- **JHU Data Archive**: [archive.data.jhu.edu](https://archive.data.jhu.edu)
- Many more institutions worldwide

## Supported URL Formats

### 1. Dataverse DOI

```yaml
src: "doi:10.7910/DVN/TJCLKP"
```

Most common format - works with any Dataverse DOI.

### 2. Full Dataverse URL

```yaml
src: "https://dataverse.harvard.edu/dataset.xhtml?persistentId=doi:10.7910/DVN/TJCLKP"
```

Direct link from Dataverse website.

### 3. Dataverse Protocol

```yaml
src: "dataverse://dataverse.harvard.edu/doi:10.7910/DVN/TJCLKP"
```

Explicitly specify server and DOI.

### 4. Alternative Installations

```yaml
src: "https://dataverse.nl/dataset.xhtml?persistentId=doi:10.34894/XXXXXX"
```

Works with any Dataverse installation.

## Configuration

### Basic Configuration

```yaml
data:
  src: "doi:10.7910/DVN/TJCLKP"
  dst: "./data"
  projectName: "harvard_dataset"
```

For DOIs without server specification, defaults to Harvard Dataverse.

### Specify Dataverse Installation

```yaml
data:
  src: "dataverse://dataverse.nl/doi:10.34894/XXXXXX"
  dst: "./data"
  projectName: "dutch_dataset"
```

### Required Fields

- **`src`**: Dataverse DOI or URL
- **`dst`**: Destination directory for downloaded files
- **`projectName`**: Name for the dataset

### Optional Fields

- **`version`**: Version identifier for cache validation

## Examples

### Example 1: Harvard Dataverse (Default)

```yaml
data:
  src: "doi:10.7910/DVN/TJCLKP"
  dst: "./data"
  projectName: "social_science_data"
```

**Command line:**

```bash
repo2data myst.yml
```

**Output:**
```
Dataverse: Example Social Science Dataset
Server: https://dataverse.harvard.edu
Files: 5
(1/5) survey_data.csv
  Downloading survey_data.csv ━━━━━━━━━━━━━━━ 100% 3.2 MB 6.1 MB/s 0:00:01
  ✓ Downloaded survey_data.csv
(2/5) codebook.pdf
  Downloading codebook.pdf ━━━━━━━━━━━━━━━ 100% 1.5 MB 5.8 MB/s 0:00:00
  ✓ Downloaded codebook.pdf
```

### Example 2: Full URL

```yaml
data:
  src: "https://dataverse.harvard.edu/dataset.xhtml?persistentId=doi:10.7910/DVN/TJCLKP"
  dst: "./data"
  projectName: "research_data"
```

### Example 3: Different Dataverse Installation

```yaml
data:
  src: "https://dataverse.nl/dataset.xhtml?persistentId=doi:10.34894/ABCDEF"
  dst: "./data"
  projectName: "netherlands_data"
```

### Example 4: Using Protocol Format

```yaml
data:
  src: "dataverse://data.aussda.at/doi:10.11587/XXXXXX"
  dst: "./data"
  projectName: "austrian_data"
```

### Example 5: Multiple Dataverse Datasets

```yaml
data:
  dataset1:
    src: "doi:10.7910/DVN/TJCLKP"
    dst: "./data"
    projectName: "harvard_study"

  dataset2:
    src: "https://dataverse.nl/dataset.xhtml?persistentId=doi:10.34894/XXXXXX"
    dst: "./data"
    projectName: "dutch_study"

  dataset3:
    src: "dataverse://dataverse.no/doi:10.18710/YYYYYY"
    dst: "./data"
    projectName: "norwegian_study"
```

### Example 6: Using from Jupyter Notebook

```python
from repo2data import Repo2Data
from repo2data.utils import locate_evidence_data
import pandas as pd

# Download data (skip if cached)
r2d = Repo2Data("myst.yml")
r2d.install()

# Locate the downloaded data
data_path = locate_evidence_data("social_science_data")

# Load data files
survey = pd.read_csv(data_path / "survey_data.csv")
print(f"Loaded {len(survey)} survey responses")

# List all downloaded files
print("\nDownloaded files:")
for file in data_path.iterdir():
    if file.is_file():
        print(f"  - {file.name} ({file.stat().st_size / 1024:.1f} KB)")
```

### Example 7: Reproducible Analysis

```python
# In notebook: repo/content/analysis/dataverse_analysis.ipynb
from repo2data.utils import locate_evidence_data
import pandas as pd
import matplotlib.pyplot as plt

# Automatically find data (works from any directory depth)
data_path = locate_evidence_data("social_science_data")

# Load and analyze
df = pd.read_csv(data_path / "survey_data.csv")

# Perform analysis
grouped = df.groupby('category')['response'].mean()
grouped.plot(kind='bar')
plt.title("Mean Responses by Category")
plt.savefig("figures/category_responses.png")

print(f"Analyzed {len(df)} responses across {len(grouped)} categories")
```

## Finding Dataverse Datasets

### Search Dataverse

1. Visit a Dataverse installation (e.g., [dataverse.harvard.edu](https://dataverse.harvard.edu))
2. Search for datasets in your field
3. Click on a dataset to view details
4. Copy the DOI or URL

### Get DOI from Dataset Page

On any Dataverse dataset page, find the DOI in the citation:

```
https://doi.org/10.7910/DVN/TJCLKP
```

Use as:
```yaml
src: "doi:10.7910/DVN/TJCLKP"
```

### Identify Dataverse Installation

From URL: `https://dataverse.harvard.edu/dataset.xhtml?persistentId=...`

Server: `dataverse.harvard.edu`

## Download Behavior

### All Files Downloaded

The Dataverse provider downloads **all files** from a dataset:
- Data files
- Documentation
- Code
- Supplementary materials

### File Organization

Files are saved to:
```
{dst}/{projectName}/
  ├── data_file1.csv
  ├── data_file2.dta
  ├── codebook.pdf
  └── readme.txt
```

Original filenames are preserved.

### Progress Tracking

Each file shows individual progress:
- File number and name
- Download progress bar
- Size and transfer speed
- Completion status

## Common Use Cases

### 1. Social Science Research

Download survey and demographic data:

```yaml
data:
  src: "doi:10.7910/DVN/EXAMPLE"
  dst: "./data"
  projectName: "survey_2024"
```

### 2. Multi-Institution Collaboration

Access datasets from different institutions:

```yaml
data:
  us_data:
    src: "doi:10.7910/DVN/USDATA"
    dst: "./data"
    projectName: "us_component"

  eu_data:
    src: "https://dataverse.nl/dataset.xhtml?persistentId=doi:10.34894/EUDATA"
    dst: "./data"
    projectName: "eu_component"
```

### 3. Longitudinal Studies

Download different waves of a study:

```yaml
data:
  wave1:
    src: "doi:10.7910/DVN/WAVE1"
    dst: "./data"
    projectName: "longitudinal_wave1"
    version: "wave1"

  wave2:
    src: "doi:10.7910/DVN/WAVE2"
    dst: "./data"
    projectName: "longitudinal_wave2"
    version: "wave2"
```

### 4. Replication Data

Download data for replication studies:

```yaml
data:
  src: "doi:10.7910/DVN/REPLICATION"
  dst: "./data"
  projectName: "replication_study_data"
```

### 5. Cross-National Studies

Access data from multiple countries:

```yaml
data:
  norway:
    src: "dataverse://dataverse.no/doi:10.18710/NORWAY"
    dst: "./data"
    projectName: "norway_data"

  austria:
    src: "dataverse://data.aussda.at/doi:10.11587/AUSTRIA"
    dst: "./data"
    projectName: "austria_data"
```

## Advantages of Dataverse Provider

1. **Global Network**: Access data from institutions worldwide
2. **Standardized Metadata**: Consistent citation and discovery
3. **Persistent DOIs**: Stable, permanent identifiers
4. **Versioning**: Track dataset updates
5. **Rich Metadata**: Comprehensive dataset descriptions
6. **Institution Backed**: Institutional repositories ensure long-term preservation
7. **API Access**: Programmatic download and metadata retrieval

## Troubleshooting

### Failed to Fetch Metadata

**Error**: `Failed to fetch Dataverse metadata`

**Solution**:
- Verify DOI is correct
- Check if dataset is public (private datasets need authentication)
- Ensure internet connection is stable
- Verify Dataverse server is accessible

### Invalid DOI Format

**Error**: `Could not parse Dataverse source`

**Solution**:
- Dataverse DOIs typically follow pattern: `10.XXXXX/DVN/XXXXXX`
- Use DOI exactly as shown on Dataverse page
- Try using full URL instead of DOI

### Server Not Accessible

**Error**: Connection to Dataverse server failed

**Solution**:
- Check if server URL is correct
- Some installations may have different URL patterns
- Try accessing the server in a web browser
- Server may be temporarily down - retry later

### No Files Found

**Error**: `No files found in Dataverse dataset`

**Solution**:
- Verify dataset has files (some datasets may only have metadata)
- Check if you have access to the files
- Dataset may be under embargo

### Download Timeout

**Error**: Download hangs or times out

**Solution**:
- Check internet connection
- Large files may take time
- Some servers may have rate limits
- Retry - Repo2Data caches successfully downloaded files

## Best Practices

1. **Use DOI for clarity**:
   ```yaml
   src: "doi:10.7910/DVN/TJCLKP"
   ```

2. **Specify server for non-Harvard Dataverse**:
   ```yaml
   src: "dataverse://dataverse.nl/doi:10.34894/XXXXXX"
   ```

3. **Add version tags**:
   ```yaml
   version: "v1.0"  # Or dataset version from Dataverse
   ```

4. **Document the source** in your README:
   ```markdown
   Data source: https://doi.org/10.7910/DVN/TJCLKP
   Harvard Dataverse, V1
   ```

5. **Cite properly**:
   - Include full Dataverse citation from dataset page
   - Credit dataset authors
   - Include dataset version

6. **Check license** before use:
   - Review terms of use on Dataverse page
   - Ensure compliance with data usage restrictions
   - Some datasets require registration or approval

## Dataset Versions

Dataverse supports versioning:
- Each version has a separate snapshot
- Versions are numbered (V1, V2, V3...)
- DOI may point to latest or specific version

**Best practice**: For reproducibility, note the version in your documentation:

```yaml
data:
  src: "doi:10.7910/DVN/TJCLKP"
  dst: "./data"
  projectName: "study_data"
  version: "V3"  # Dataverse version V3
```

## Authentication for Restricted Access

For restricted or embargoed datasets:

Some datasets require:
- Registration and approval
- Data use agreements
- Institutional access

Contact dataset owner for access instructions. The Dataverse API supports authentication, but this is beyond basic Repo2Data usage.

## Metadata Access

Dataverse provides rich metadata through its API. Future enhancements could expose this programmatically.

Current metadata includes:
- Dataset title
- Authors and contributors
- Description
- Subject/keywords
- Related publications
- Geographic coverage
- Time period

## Dataverse API

The Dataverse provider uses the Dataverse API:
- Endpoint: `{server}/api/datasets/:persistentId`
- Public datasets require no authentication
- Returns comprehensive metadata
- File download via: `{server}/api/access/datafile/{fileId}`

## Finding Dataverse Installations

Major Dataverse installations:

**North America:**
- Harvard Dataverse (largest): dataverse.harvard.edu
- UNC Dataverse: dataverse.unc.edu
- Johns Hopkins: archive.data.jhu.edu

**Europe:**
- DataverseNL: dataverse.nl
- DataverseNO: dataverse.no
- AUSSDA (Austria): data.aussda.at

**Others:**
- See complete list: [https://dataverse.org/installations](https://dataverse.org/installations)

## Related Resources

- [Dataverse Project](https://dataverse.org/)
- [Harvard Dataverse](https://dataverse.harvard.edu)
- [Dataverse API Guide](https://guides.dataverse.org/en/latest/api/)
- [Find Dataverse Installations](https://dataverse.org/installations)

## Comparison: Dataverse vs Other Repositories

**Dataverse advantages:**
- Institutional backing and long-term preservation
- Rich metadata standards
- Institutional repositories for sensitive/restricted data
- Integration with institution systems

**Consider alternatives:**
- **Zenodo**: For general-purpose, large files, GitHub integration
- **Figshare**: For figures, presentations, smaller datasets
- **OSF**: For full project management and collaboration

## Back to Main Guide

Return to the [main documentation](./data.md) for general Repo2Data features and other providers.
