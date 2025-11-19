# Google Drive Provider

The Google Drive provider enables downloading files and folders from Google Drive, making it easy to work with data shared via Google Drive links.

## What is Google Drive?

Google Drive is a cloud storage service that allows users to store files, share them, and collaborate. Many researchers use Google Drive to share datasets, supplementary materials, and collaborative project files.

## Installation

### Install Repo2Data

```bash
pip install repo2data
```

### Install gdown

The Google Drive provider requires `gdown`, a tool for downloading files from Google Drive:

```bash
pip install gdown
```

## How It Works

The Google Drive provider:

1. **Detects Google Drive URLs** containing `drive.google.com`
2. **Uses `gdown`** to handle Google Drive authentication and downloads
3. **Downloads files** to your specified destination
4. **Supports both files and folders** (with appropriate share settings)

## Supported URL Formats

### 1. Direct File Link

```
https://drive.google.com/file/d/FILE_ID/view?usp=sharing
```

### 2. Download Link

```
https://drive.google.com/uc?id=FILE_ID
```

### 3. Folder Link

```
https://drive.google.com/drive/folders/FOLDER_ID?usp=sharing
```

## Configuration

### Basic Configuration - Single File

```yaml
data:
  src: "https://drive.google.com/file/d/1a2B3c4D5e6F7g8H9i0J/view?usp=sharing"
  dst: "./data"
  projectName: "gdrive_dataset"
```

### Required Fields

- **`src`**: Google Drive URL (file or folder)
- **`dst`**: Destination directory
- **`projectName`**: Name for the dataset

### Optional Fields

- **`version`**: Version identifier for cache management

## Getting Google Drive Share Links

### For Files

1. Open Google Drive
2. Right-click on the file
3. Select "Get link" or "Share"
4. Set sharing to "Anyone with the link can view"
5. Copy the link
6. Use the link in your configuration

### For Folders

1. Right-click on the folder in Google Drive
2. Select "Get link"
3. Set to "Anyone with the link can view"
4. Copy the folder link
5. Use in your configuration

**Important**: Files and folders must be set to "Anyone with the link" for `gdown` to download them.

## Examples

### Example 1: Download a Single File

```yaml
data:
  src: "https://drive.google.com/file/d/1BxT3jK9mL2nP4qR5sT6uV7wX8yZ9/view"
  dst: "./data"
  projectName: "research_data"
```

**Command line:**

```bash
repo2data myst.yml
```

### Example 2: Download Using File ID

You can extract the file ID and use `gdown` URL format:

```yaml
data:
  src: "https://drive.google.com/uc?id=1BxT3jK9mL2nP4qR5sT6uV7wX8yZ9"
  dst: "./data"
  projectName: "research_data"
```

### Example 3: Download from Jupyter Notebook

```python
from repo2data import Repo2Data
from repo2data.utils import locate_evidence_data
import pandas as pd

# Download data (skip if already cached)
r2d = Repo2Data("myst.yml")
r2d.install()

# Locate the data
data_path = locate_evidence_data("research_data")

# Load the downloaded file
# gdown preserves original filename
csv_file = next(data_path.glob("*.csv"))  # Find CSV file
df = pd.read_csv(csv_file)

print(f"Loaded {len(df)} rows of data")
```

### Example 4: Multiple Google Drive Files

Download several files in one configuration:

```yaml
data:
  raw_data:
    src: "https://drive.google.com/file/d/FILE_ID_1/view"
    dst: "./data"
    projectName: "raw_experimental_data"

  processed_data:
    src: "https://drive.google.com/file/d/FILE_ID_2/view"
    dst: "./data"
    projectName: "processed_data"

  metadata:
    src: "https://drive.google.com/file/d/FILE_ID_3/view"
    dst: "./data"
    projectName: "experimental_metadata"
```

### Example 5: Large Dataset from Drive

For large files, `gdown` shows progress:

```yaml
data:
  src: "https://drive.google.com/file/d/LARGE_FILE_ID/view"
  dst: "./data"
  projectName: "large_imaging_dataset"
  version: "v2.0"
```

### Example 6: Workflow with Located Data

```python
# In notebook: repo/content/analysis/preprocessing.ipynb
from repo2data.utils import locate_evidence_data
import numpy as np
from pathlib import Path

# Find the data (works from any directory in repo)
data_path = locate_evidence_data("research_data")

# Process all data files
for npy_file in data_path.glob("*.npy"):
    data = np.load(npy_file)
    # Your processing here
    print(f"Processed {npy_file.name}: shape {data.shape}")
```

## Download Behavior

### File Naming

`gdown` preserves the original filename from Google Drive:
- File downloads to: `{dst}/{projectName}/original_filename.ext`

### Progress Display

For files, `gdown` shows:
- Download progress
- Transfer speed
- File size

### Folders

For Google Drive folders, `gdown` can download entire folder structure (requires proper permissions).

## Common Use Cases

### 1. Collaborative Research Data

Download data shared by collaborators:

```yaml
data:
  src: "https://drive.google.com/file/d/COLLABORATOR_FILE_ID/view"
  dst: "./data"
  projectName: "collaboration_data"
```

### 2. Supplementary Materials

Download supplementary data from papers where authors used Google Drive:

```yaml
data:
  src: "https://drive.google.com/file/d/PAPER_SUPPLEMENT_ID/view"
  dst: "./data"
  projectName: "paper_supplement"
```

### 3. Lab Shared Resources

Access shared lab datasets:

```yaml
data:
  src: "https://drive.google.com/file/d/LAB_SHARED_ID/view"
  dst: "./data"
  projectName: "lab_reference_data"
```

### 4. Large Imaging Datasets

Download large neuroimaging or microscopy data:

```yaml
data:
  src: "https://drive.google.com/file/d/IMAGING_DATA_ID/view"
  dst: "./data"
  projectName: "microscopy_images"
  version: "experiment_2024_01"
```

## Advantages of Google Drive Provider

1. **Familiar Platform**: Many researchers already use Google Drive
2. **Easy Sharing**: Simple link sharing mechanism
3. **Large File Support**: Google Drive handles large files well
4. **No Special Account**: Download public links without Google account (in most cases)
5. **Automatic Integration**: No manual download steps

## Troubleshooting

### gdown Not Installed

**Error**: `FileNotFoundError: gdown is not installed`

**Solution**: Install gdown:

```bash
pip install gdown
```

### Permission Denied / Access Restricted

**Error**: `gdown failed` with permission error

**Solution**:
- Ensure file is shared as "Anyone with the link can view"
- Check if file owner changed sharing settings
- For restricted files, you may need to authenticate with `gdown`

### File Too Large / Quota Exceeded

**Error**: Google Drive quota exceeded or file too large

**Solution**:
- Large files (>100MB) may trigger virus scan warning
- Try again later if quota exceeded
- Owner may need to adjust sharing settings
- Consider splitting large files or using alternative hosting

### Cannot Download Folder

**Error**: Folder download fails

**Solution**:
- Ensure folder is shared properly ("Anyone with the link")
- Some folder structures may not be supported
- Consider downloading as ZIP from Google Drive, then hosting the ZIP

### Download Stalls or Times Out

**Error**: Download hangs or times out

**Solution**:
- Check internet connection
- Large files may take time - be patient
- Google Drive may temporarily limit download speed
- Retry the download - Repo2Data will use cached version if available

## Best Practices

1. **Use descriptive project names**:
   ```yaml
   projectName: "imaging_dataset_2024"  # Good
   projectName: "gdrive1"  # Avoid
   ```

2. **Set proper sharing permissions** before sharing:
   - "Anyone with the link can view" for public datasets
   - Consider using service account for production workflows

3. **Add version identifiers** for changing datasets:
   ```yaml
   version: "v2.1"
   ```

4. **Document the source** in your README:
   ```markdown
   Data source: https://drive.google.com/file/d/FILE_ID/view
   ```

5. **Consider alternatives for permanent storage**:
   - Google Drive links can break if file is moved/deleted
   - For published data, consider Zenodo, Figshare, or Dataverse
   - Use Google Drive for active collaborations and working data

## Alternative: Manual Download

If `gdown` has issues, you can manually download and use Repo2Data's cache:

1. Download file from Google Drive manually
2. Place in: `{dst}/{projectName}/`
3. Repo2Data will detect it via cache on subsequent runs

## Authentication for Private Files

For files requiring Google account authentication:

```bash
# Install gdown with authentication support
pip install gdown[authentication]

# Authenticate (opens browser)
gdown --auth

# Then use Repo2Data normally
repo2data myst.yml
```

## Limitations

1. **Public sharing required**: Files must be publicly shared for simple use
2. **Link stability**: Links can break if file is moved or permissions change
3. **Large file virus scan**: Google may require manual virus scan confirmation for large files
4. **Quota limits**: Google Drive has download quotas that may be hit for popular files

## Related Resources

- [gdown Documentation](https://github.com/wkentaro/gdown)
- [Google Drive Help](https://support.google.com/drive)
- [Sharing Files on Google Drive](https://support.google.com/drive/answer/2494822)

## Back to Main Guide

Return to the [main documentation](./data.md) for general Repo2Data features and other providers.
