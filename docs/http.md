# HTTP/HTTPS Provider

The HTTP/HTTPS provider enables downloading files from any public HTTP or HTTPS URL, making it the most flexible provider for accessing publicly available datasets.

## What is the HTTP Provider?

The HTTP provider is a generic downloader that works with any standard HTTP/HTTPS URL. It's automatically used when your source URL doesn't match any specialized provider (Git, Google Drive, OSF, etc.).

This provider is ideal for:
- Direct file downloads from web servers
- Public datasets hosted on institutional servers
- Download links from data sharing platforms
- URLs to compressed archives (automatically extracted)

## Installation

```bash
pip install repo2data
```

No additional dependencies required - uses Python's `requests` library.

## How It Works

The HTTP provider:

1. **Detects HTTP/HTTPS URLs** that don't match specialized providers
2. **Downloads with retry logic** and exponential backoff
3. **Shows progress bars** with size, speed, and ETA
4. **Verifies checksums** if provided
5. **Checks disk space** before downloading
6. **Uses atomic downloads** (.tmp files, renamed on success)
7. **Auto-extracts archives** (.zip, .tar.gz, etc.)

## Supported URL Formats

Any HTTP or HTTPS URL:

```
http://example.com/data/dataset.zip
https://university.edu/research/data/experiment.tar.gz
https://cdn.example.org/files/image_dataset.zip
```

**Exclusions:** URLs matching specialized providers are handled by those providers:
- `.git` URLs → DataLad provider
- `drive.google.com` → Google Drive provider
- `osf.io` → OSF provider
- Zenodo/Figshare/Dataverse DOIs → Their respective providers

## Configuration

### Basic Configuration

```yaml
data:
  src: "https://example.com/datasets/research_data.zip"
  dst: "./data"
  projectName: "research_dataset"
```

### With Checksum Verification

```yaml
data:
  src: "https://example.com/datasets/research_data.zip"
  dst: "./data"
  projectName: "research_dataset"
  checksum: "a7b3c4d5e6f7890123456789abcdef1234567890abcdef1234567890abcdef12"
  checksum_algorithm: "sha256"
```

### Required Fields

- **`src`**: HTTP or HTTPS URL to the file
- **`dst`**: Destination directory
- **`projectName`**: Name for the dataset

### Optional Fields

- **`version`**: Version identifier for cache management
- **`checksum`**: Expected checksum hash for verification
- **`checksum_algorithm`**: Hash algorithm (sha256, md5, sha1)

## Examples

### Example 1: Download ZIP Archive

```yaml
data:
  src: "https://university.edu/data/experiment_2024.zip"
  dst: "./data"
  projectName: "experiment_2024"
```

The ZIP file will be automatically extracted and then deleted.

**Command line:**

```bash
repo2data myst.yml
```

### Example 2: Download with Checksum Verification

```yaml
data:
  src: "https://example.com/datasets/critical_data.tar.gz"
  dst: "./data"
  projectName: "critical_data"
  checksum: "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
  checksum_algorithm: "sha256"
```

Data integrity will be verified after download.

### Example 3: Multiple HTTP Downloads

```yaml
data:
  raw_data:
    src: "https://server1.edu/data/raw_experiment.zip"
    dst: "./data"
    projectName: "raw_experiment"

  processed_data:
    src: "https://server2.edu/data/processed_results.tar.gz"
    dst: "./data"
    projectName: "processed_results"

  supplementary:
    src: "https://cdn.example.org/supplements/figures.zip"
    dst: "./data"
    projectName: "supplementary_figures"
```

### Example 4: Using from Jupyter Notebook

```python
from repo2data import Repo2Data
from repo2data.utils import locate_evidence_data
import pandas as pd

# Download data (skip if cached)
r2d = Repo2Data("myst.yml")
r2d.install()

# Locate the downloaded and extracted data
data_path = locate_evidence_data("experiment_2024")

# Load data
csv_file = data_path / "experiment_results.csv"
df = pd.read_csv(csv_file)
print(f"Loaded {len(df)} rows of data")
```

### Example 5: Direct File (Non-Archive)

```yaml
data:
  src: "https://raw.githubusercontent.com/user/repo/main/data.csv"
  dst: "./data"
  projectName: "github_raw_data"
```

For non-archive files, the file is simply downloaded without extraction.

### Example 6: Large Dataset with Version

```yaml
data:
  src: "https://datasets.example.org/imaging/brain_scans_v2.zip"
  dst: "./data"
  projectName: "brain_imaging"
  version: "v2.0"
```

Changing the version will trigger re-download even if project name is the same.

### Example 7: Reproducible Analysis Workflow

```python
# In notebook: repo/content/analysis/imaging_analysis.ipynb
from repo2data.utils import locate_evidence_data
import nibabel as nib
import numpy as np

# Automatically find extracted data
data_path = locate_evidence_data("brain_imaging")

# Process all NIfTI files
nifti_files = list(data_path.glob("**/*.nii.gz"))
print(f"Found {len(nifti_files)} brain scans")

for nifti_file in nifti_files:
    img = nib.load(str(nifti_file))
    data = img.get_fdata()
    print(f"{nifti_file.name}: shape {data.shape}")
```

## Download Features

### Progress Tracking

Downloads show detailed progress information:

```
  Downloading research_data.zip ━━━━━━━━━━━━━━━━━━━━━ 45% 23.5 MB/52.0 MB 8.3 MB/s 0:00:03
```

Shows:
- Filename
- Progress bar (persists after completion)
- Percentage complete
- Downloaded size / Total size
- Transfer speed
- Estimated time remaining

### Retry Logic

The provider automatically retries failed downloads:
- **3 retry attempts** with exponential backoff
- Delays: 5s, 10s, 20s between retries
- Handles network errors gracefully
- Clear error messages after all retries exhausted

### Checksum Verification

Ensure data integrity:

```yaml
checksum: "hash_value"
checksum_algorithm: "sha256"  # or "md5" or "sha1"
```

After download, the file is verified before extraction. If checksum fails:
- Temporary file is deleted
- Clear error message with expected vs actual hash
- No corrupted data left behind

**Generate checksums:**

```bash
# Linux/macOS
sha256sum filename
md5sum filename

# Windows
certutil -hashfile filename SHA256

# Python
from repo2data.utils import compute_checksum
hash_val = compute_checksum("path/to/file", "sha256")
print(hash_val)
```

### Disk Space Checking

Before starting download:
- Checks available disk space
- Requires file size + 100MB buffer
- Raises clear error if insufficient space
- Prevents partial downloads that fill disk

### Atomic Downloads

Safe download process:
1. Download to `.tmp` extension
2. Verify checksum (if provided)
3. Rename to final name only on success
4. Failed downloads auto-cleanup temp files

No corrupted or partial files left behind!

### Automatic Archive Extraction

Supported formats (via `patool`):
- `.zip` - ZIP archives
- `.tar` - TAR archives
- `.tar.gz`, `.tgz` - Gzipped TAR
- `.tar.bz2`, `.tbz2` - Bzip2 TAR
- `.tar.xz` - XZ TAR
- `.rar` - RAR archives
- `.7z` - 7-Zip archives
- Many more formats

After successful extraction:
- Archive file is deleted (saves space)
- macOS junk files automatically removed (`.DS_Store`, `__MACOSX/`, `._*`)

Install `patool` for archive support:
```bash
pip install patool
```

### Filename Detection

The provider intelligently determines filenames:

1. **From Content-Disposition header** (if present)
2. **From URL** (removes query parameters)
3. **From Content-Type** (guesses extension)
4. **Default**: `download.bin` with appropriate extension

## Common Use Cases

### 1. Institutional Data Repositories

Download from university or lab servers:

```yaml
data:
  src: "https://lab.university.edu/datasets/study_2024/data.zip"
  dst: "./data"
  projectName: "university_study"
```

### 2. GitHub Raw Files

Download specific files from GitHub:

```yaml
data:
  src: "https://raw.githubusercontent.com/user/repo/main/data/dataset.csv"
  dst: "./data"
  projectName: "github_dataset"
```

For entire repos, use Datalad provider with `.git` URL instead.

### 3. CDN-Hosted Datasets

Download from content delivery networks:

```yaml
data:
  src: "https://cdn.example.com/datasets/ml_training_data.tar.gz"
  dst: "./data"
  projectName: "ml_training"
```

### 4. Direct Download Links

Many platforms provide direct download links:

```yaml
data:
  src: "https://downloads.example.org/files/dataset_v1.zip"
  dst: "./data"
  projectName: "dataset_v1"
  version: "1.0"
```

### 5. Compressed Archives

Automatically extracted:

```yaml
data:
  src: "https://data.example.org/experiments/compressed_data.tar.gz"
  dst: "./data"
  projectName: "experimental_data"
```

Files extracted to `./data/experimental_data/`

### 6. Verified Downloads

Critical data with checksum verification:

```yaml
data:
  src: "https://critical.example.org/data.zip"
  dst: "./data"
  projectName: "verified_data"
  checksum: "sha256_hash_here"
  checksum_algorithm: "sha256"
```

## Advantages of HTTP Provider

1. **Universal**: Works with any HTTP/HTTPS URL
2. **No dependencies**: Uses standard Python libraries
3. **Robust**: Retry logic handles network issues
4. **Safe**: Atomic downloads, checksum verification
5. **Smart**: Auto-extraction, filename detection
6. **User-friendly**: Progress bars, clear errors
7. **Efficient**: Disk space checking, cleanup

## Troubleshooting

### Connection Timeout

**Error**: `Timeout after 30 seconds`

**Solution**:
- Check internet connection
- URL may be slow or unreachable
- Provider retries automatically (3 attempts)
- Increase timeout if you modify the code

### File Not Found (404)

**Error**: `File not found (404): URL`

**Solution**:
- Verify URL is correct
- Check if file still exists at that location
- Copy URL directly from browser
- Ensure no typos in URL

### Access Forbidden (403)

**Error**: `Access forbidden (403): URL`

**Solution**:
- File may require authentication
- Check if URL requires login
- Server may block automated downloads
- Try accessing in browser first

### Checksum Mismatch

**Error**: `Checksum mismatch for file`

**Solution**:
- File may be corrupted during download
- Provider will retry automatically
- Verify checksum value is correct
- Re-generate checksum from source

### Insufficient Disk Space

**Error**: `OSError: Insufficient disk space`

**Solution**:
- Free up disk space (need file_size + 100MB)
- Change `dst` to location with more space
- Check with: `df -h` (Linux/macOS) or `dir` (Windows)

### SSL Certificate Error

**Error**: SSL verification failed

**Solution**:
- Update Python's certifi package: `pip install --upgrade certifi`
- Check system time is correct
- Server may have expired SSL certificate

### Archive Extraction Failed

**Error**: patool extraction error

**Solution**:
- Install patool: `pip install patool`
- Ensure archive file is valid (not corrupted)
- Check supported formats
- Try downloading archive manually to verify

## Best Practices

1. **Always use HTTPS** when available:
   ```yaml
   src: "https://example.com/data.zip"  # Secure
   # Not: http://example.com/data.zip   # Avoid
   ```

2. **Add checksums for critical data**:
   ```yaml
   checksum: "sha256_hash"
   checksum_algorithm: "sha256"
   ```

3. **Use version tags** for reproducibility:
   ```yaml
   version: "v1.0"
   ```

4. **Document the source** in your README:
   ```markdown
   Data source: https://example.com/datasets/study_2024.zip
   Downloaded: 2024-01-15
   ```

5. **Prefer specialized providers** when available:
   - For Zenodo → use Zenodo DOI
   - For Figshare → use Figshare DOI
   - For GitHub repos → use `.git` URL with Datalad
   - For S3 → use `s3://` URL with S3 provider

6. **Test URLs manually** before adding to config:
   - Open URL in browser to verify it works
   - Check file size for disk space planning
   - Generate checksum from downloaded file

## URL Best Practices

**Good URLs:**
```yaml
# Direct file link
src: "https://data.example.org/datasets/file.zip"

# GitHub raw content
src: "https://raw.githubusercontent.com/user/repo/main/data.csv"

# CDN with specific version
src: "https://cdn.example.com/v2/datasets/data.tar.gz"
```

**Avoid:**
```yaml
# Shortened URLs (may change)
src: "https://bit.ly/abc123"

# URLs requiring authentication
src: "https://private.example.com/data.zip"

# Dynamic URLs (may expire)
src: "https://example.com/download?token=temp123"
```

## Security Considerations

1. **Only download from trusted sources**
2. **Use HTTPS to prevent man-in-the-middle attacks**
3. **Verify checksums for critical data**
4. **Be cautious with executable files**
5. **Check file contents** before running code from downloads

## Performance Tips

- **Large files**: Progress bars help track long downloads
- **Slow connections**: Retry logic handles interruptions
- **Multiple files**: Download in parallel using multiple configs
- **Compressed data**: Use `.tar.gz` or `.zip` to reduce transfer size

## Related Resources

- [Python requests documentation](https://docs.python-requests.org/)
- [HTTP Status Codes](https://developer.mozilla.org/en-US/docs/Web/HTTP/Status)
- [patool supported formats](https://wummel.github.io/patool/)

## Back to Main Guide

Return to the [main documentation](./data.md) for general Repo2Data features and other providers.
